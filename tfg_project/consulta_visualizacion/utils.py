from .sparql_query import SPARQLQuery
import requests
import os
import json

# ---
# Función para obtener los datatsets de Fuseki
def obtener_datasets():
    datasets_url = f"http://localhost:3030/$/datasets"
    response = requests.get(datasets_url, headers={"Accept": "application/json"})
    # Si hay datasets, se devuelve el nombre y si no, nada
    if response.status_code == 200:
        datasets = response.json().get("datasets", [])
        return [dataset["ds.name"].strip("/") for dataset in datasets]  # Lista de nombres de datasets
    return [] # Si no hay, lista vacía

# ---
# Función para truncar las urls y conseguir un nombre legible en el caso de que no haya labels disponibles en los datos
def obtener_nombre_uri(uri):
    # Extrae el último fragmento de una URI, usando # o / como separadores
    return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]


# --
# GENERAR ARCHIVOS JSON PARA MEJORAR EL RENDIMIENTO

# Carpeta para almacenar los archivos JSON
JSON_DIR = "json_cache" 
# Comprueba si el directorio existe, si no lo crea para evitar errores
if not os.path.exists(JSON_DIR):
    os.makedirs(JSON_DIR)

# Genera el JSON con los datos del dataset 
def generar_json_dataset(selected_dataset):
    
    # Asegurar que el directorio JSON existe antes de generar el archivo
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
        
    sparql = SPARQLQuery(selected_dataset) #Endpoint
    
    # Diccionario donde almacenamos los datos
    data = {}
    
    # MÉTRICAS GENERALES
    consultas_metricas = {
        "num_tripletas": "SELECT (COUNT(*) AS ?numero) WHERE { ?s ?p ?o }",
        "num_clases": "SELECT (COUNT(DISTINCT ?class) AS ?numero) WHERE { ?s a ?class }",
        "num_instancias": "SELECT (COUNT(DISTINCT ?s) AS ?numero) WHERE { ?s a ?type }",
        "num_propiedades": "SELECT (COUNT(DISTINCT ?p) AS ?numero) WHERE { ?s ?p ?o }"
    }
    
    # Ejecutar métricas y procesar los resultados
    for key, query in consultas_metricas.items():
        try:
            resultado = sparql.ejecutar_consulta(query)
            data[key] = int(resultado["results"]["bindings"][0]["numero"]["value"]) if resultado["results"]["bindings"] else 0
        except Exception as e:
            print(f"Error en {key}: {e}")
            data[key] = 0
    
    # CLASES Y PROPIEDADES
    consultas_diccionarios = {
        "clases": """SELECT DISTINCT ?class (SAMPLE(REPLACE(STR(?class), "^.*[#/]", "")) AS ?label) WHERE { 
                        ?s a ?class .} 
                    GROUP BY ?class
                    ORDER BY ?label""",
        "propiedades": """SELECT DISTINCT ?propiedad (SAMPLE(REPLACE(STR(?propiedad), "^.*[#/]", "")) AS ?label) WHERE { 
                            ?s ?propiedad ?o .} 
                        GROUP BY ?propiedad
                        ORDER BY ?label"""
    }
    
    # Ejecutar consultas y procesar resultados en forma de diccionario {label: URI}
    try:
        # Clases
        resultado_clases = sparql.ejecutar_consulta(consultas_diccionarios["clases"])
        data["clases"] = {res["label"]["value"]: res["class"]["value"] for res in resultado_clases["results"]["bindings"] if "label" in res and "class" in res}
        
        # Propiedades
        resultado_propiedades = sparql.ejecutar_consulta(consultas_diccionarios["propiedades"])
        data["propiedades"] = {res["label"]["value"]: res["propiedad"]["value"] for res in resultado_propiedades["results"]["bindings"] if "label" in res and "propiedad" in res}
    except Exception as e:
        print(f"Error en clases o propiedades: {e}")
        data["clases"] = {}
        data["propiedades"] = {}
            
    ## DISTRIBUCIÓN DE CLASES Y PROPIEDADES
    consultas_distribucion = {
        "distribucion_clases": """SELECT 
                        (SAMPLE(REPLACE(STR(?class), "^.*[#/]", "")) AS ?label)
                        (COUNT(?s) AS ?count)
                    WHERE { ?s a ?class } 
                    GROUP BY ?class
                    ORDER BY DESC(?count)""",
        "distribucion_propiedades": """SELECT 
                            (SAMPLE(REPLACE(STR(?p), "^.*[#/]", "")) AS ?label)
                            (COUNT(?s) AS ?count)
                        WHERE { ?s ?p ?o } 
                        GROUP BY ?p
                        ORDER BY DESC(?count)"""
    }

    # Ejecutar consultas y almacenar listas de tuplas (label, count)
    for key, query in consultas_distribucion.items():
        try:
            resultado = sparql.ejecutar_consulta(query)
            data[key] = [
                (res.get("label", {}).get("value", "Desconocido"), int(res.get("count", {}).get("value", 0)))
                for res in resultado["results"]["bindings"]
                if "label" in res and "count" in res
            ]
        except Exception as e:
            print(f"Error en {key}: {e}")
            data[key] = []
            
    # RELACIONES ENTRE PROPIEDADES Y CLASES
    consultas_relaciones = {
        "relacion_propiedades_clases": """SELECT 
                                    (SAMPLE(REPLACE(STR(?s_class), "^.*[#/]", "")) AS ?s_class_label)
                                    (SAMPLE(REPLACE(STR(?p), "^.*[#/]", "")) AS ?p_label)
                                    (COUNT(*) AS ?count)
                                WHERE { 
                                    ?s ?p ?o .
                                    ?s a ?s_class .
                                } 
                                GROUP BY ?s_class ?p
                                ORDER BY DESC(?count)""",
        "relacion_instancias_clases": """SELECT 
                                    (SAMPLE(REPLACE(STR(?clase_origen), "^.*[#/]", "")) AS ?clase_origen_label)
                                    (SAMPLE(REPLACE(STR(?clase_destino), "^.*[#/]", "")) AS ?clase_destino_label)
                                    (COUNT(*) AS ?count)
                                WHERE { 
                                    ?instancia_origen a ?clase_origen .
                                    ?instancia_destino a ?clase_destino .
                                    ?instancia_origen ?p ?instancia_destino .
                                } 
                                GROUP BY ?clase_origen ?clase_destino
                                ORDER BY DESC(?count)"""
    }

    # Ejecutar consultas y almacenar listas de tuplas
    for key, query in consultas_relaciones.items():
        try:
            resultado = sparql.ejecutar_consulta(query)
            data[key] = [
                (
                    res.get("s_class_label" if "propiedades" in key else "clase_origen_label", {}).get("value", "Desconocido"),
                    res.get("p_label" if "propiedades" in key else "clase_destino_label", {}).get("value", "Desconocido"),
                    int(res.get("count", {}).get("value", 0))
                )
                for res in resultado["results"]["bindings"]
                if all(k in res for k in ["s_class_label", "p_label", "count"]) or all(k in res for k in ["clase_origen_label", "clase_destino_label", "count"])
            ]
        except Exception as e:
            print(f"Error en {key}: {e}")
            data[key] = []
    
    # Guardar el JSON
    try:
        # Nombre del JSON del dataset
        json_path = os.path.join(JSON_DIR, f"{selected_dataset}.json")
        # Se abre el archivo y se sobreescribe con los datos
        with open(json_path, "w") as json_file:
            json.dump(data, json_file)
    # Mensaje de excepción
    except Exception as e:
        print(f"Error generando JSON: {e}")
    return data

# Carga el JSON del dataset si existe
def cargar_json_dataset(selected_dataset):
    json_path = os.path.join(JSON_DIR, f"{selected_dataset}.json")
    if os.path.exists(json_path):
        with open(json_path, "r") as json_file:
            return json.load(json_file)
    return None