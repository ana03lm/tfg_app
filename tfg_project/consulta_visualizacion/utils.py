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
def generar_json_dataset(selected_dataset, actualizar_estado=lambda x: None):
    
    # Asegurar que el directorio JSON existe antes de generar el archivo
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
        
    sparql = SPARQLQuery(selected_dataset) #Endpoint
    
    # Diccionario donde almacenamos los datos
    data = {}
    
    # MÉTRICAS GENERALES
    # Función para imprimir mensajes de progreso en la pantalla de carga
    actualizar_estado("Obteniendo métricas generales...")
    # Construcción de la consulta
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
    actualizar_estado("Analizando clases y propiedades...")
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
    actualizar_estado("Generando distribuciones...")
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
    actualizar_estado("Generando mapas de calor...")
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
        actualizar_estado("Guardando el JSON...")
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


# ---
# Genera una consulta SPARQL a partir de los parámetros proporcionados por el usuario
def busqueda(filtro_clase, filtro_sujeto, filtro_propiedad, filtro_objeto, modo_filtro, clases_dict=None, uri_real_clase=None):

    # Si el modo de filtrado es AND, construimos una consulta donde todas las condiciones deben cumplirse
    if modo_filtro == "AND":
        condiciones = ["?s ?p ?o"]  # Base de la consulta. Se asegura que haya una estructura de tripleta
        
        # Si estamos explorando una clase específica, añadimos su filtro
        if uri_real_clase:
            condiciones.append(f"?s a <{uri_real_clase}>")

        # Si hay valores en los filtros, se van añadiendo en las condiciones.
        # Para ello se utilizan los filtros SPARQL, que filtrarán el parámetro por el valor insertado por el usuario con CONTAINS y LCASE 
        # Esto permite un filtrado más intuitivo y más cercano al lenguaje natural
        if filtro_clase and clases_dict:
            if filtro_clase in clases_dict.keys():
                condiciones.append(f"?s a <{clases_dict[filtro_clase]}>")
            if filtro_clase in clases_dict.values():
                condiciones.append(f"?s a <{filtro_clase}>")

        if filtro_sujeto:
            condiciones.append(f'FILTER(CONTAINS(LCASE(STR(?s)), LCASE("{filtro_sujeto}")))')

        if filtro_propiedad:
            condiciones.append(f'FILTER(CONTAINS(LCASE(STR(?p)), LCASE("{filtro_propiedad}")))')

        if filtro_objeto:
            condiciones.append(f'FILTER(CONTAINS(LCASE(STR(?o)), LCASE("{filtro_objeto}")))')

        # Combina las condiciones
        # Ordena alfabéticamente por label
        query = f"""
            SELECT DISTINCT ?s ?label WHERE {{
                {' . '.join(condiciones)}
                OPTIONAL {{ ?s ?anyPredicate ?label . FILTER(REGEX(STR(?anyPredicate), "label", "i")) }}
            }}
            ORDER BY LCASE(STR(?label))  
        """

    # Si el modo es OR, al menos una de las condiciones debe cumplirse
    else:
        condiciones_union = []
        # Se construyen de nuevo las condiciones, pero esta vez se harán subconsultas
        if filtro_clase and clases_dict:
            if filtro_clase in clases_dict.keys():
                condiciones_union.append(f'{{ ?s a <{clases_dict[filtro_clase]}> . ?s ?p ?o }}')
            if filtro_clase in clases_dict.values():
                condiciones_union.append(f'{{ ?s a <{filtro_clase}> . ?s ?p ?o }}')

        if filtro_sujeto:
            condiciones_union.append(f'{{ ?s ?p ?o . FILTER(CONTAINS(LCASE(STR(?s)), LCASE("{filtro_sujeto}"))) }}')

        if filtro_propiedad:
            condiciones_union.append(f'{{ ?s ?p ?o . FILTER(CONTAINS(LCASE(STR(?p)), LCASE("{filtro_propiedad}"))) }}')

        if filtro_objeto:
            condiciones_union.append(f'{{ ?s ?p ?o . FILTER(CONTAINS(LCASE(STR(?o)), LCASE("{filtro_objeto}"))) }}')

        # Se construye la consulta combinando las subconsultas con UNION
        # Asegurar que hay al menos una condición para evitar un UNION vacío
        if condiciones_union:
            query = f"""
                SELECT DISTINCT ?s ?label WHERE {{
                    {f"?s a <{uri_real_clase}> ." if uri_real_clase else ""}
                    {' UNION '.join(condiciones_union)}
                    OPTIONAL {{ ?s ?anyPredicate ?label . FILTER(REGEX(STR(?anyPredicate), "label", "i")) }}
                }}
                ORDER BY LCASE(STR(?label))
            """
        else:
            # Si no hay filtros, obtener todas las instancias disponibles
            query = """
                SELECT DISTINCT ?s ?label WHERE {
                    ?s ?p ?o .
                    OPTIONAL { ?s ?anyPredicate ?label . FILTER(REGEX(STR(?anyPredicate), "label", "i")) }
                }
                ORDER BY LCASE(STR(?label))  # Ordena alfabéticamente por label
            """

    return query
