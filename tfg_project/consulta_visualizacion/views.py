import os
import requests
from django.shortcuts import render, redirect
from .forms import RDFUploadForm, DatasetSelectionForm
import json
from .sparql_query import SPARQLQuery  # Importamos la clase para consultas SPARQL
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import urllib.parse

# URL base de Fuseki
URL_FUSEKI = "http://localhost:3030"

# ---
# Función para obtener los datatsets de Fuseki
def obtener_datasets():
    datasets_url = f"{URL_FUSEKI}/$/datasets"
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

# ---
# Función de creación y subida del dataset a Apache Jena Fuseki
def upload_rdf(request):
    if request.method == "POST":  # Se comprueba que el método es POST
        form = RDFUploadForm(request.POST, request.FILES) 
        if form.is_valid():
            uploaded_file = request.FILES["rdf_file"]  # Se captura el archivo enviado
            dataset_name = os.path.splitext(uploaded_file.name)[0]  # Se captura el nombre del archivo para posteriormente nombrar el dataset
            
            # Tipos MIME admitidos
            TIPOS_ARCHIVOS = {
                "ttl": "text/turtle",
                "rdf": "application/rdf+xml",
                "nt": "application/n-triples"
            }
            
            # Se captura la extensión del archivo y se hace la correspondencia con su tipo Mime
            file_extension = uploaded_file.name.split(".")[-1].lower() 
            mime_type = TIPOS_ARCHIVOS.get(file_extension, "application/octet-stream")
            
            # Se lee el archivo
            rdf_data = uploaded_file.read()
            
            # Crear el dataset antes de subir datos
            create_dataset_url = f"{URL_FUSEKI}/$/datasets"
            dataset_payload = {"dbName": dataset_name, "dbType": "tdb2"} #Con persistencia

            create_response = requests.post(
                create_dataset_url,
                data=dataset_payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            # Códigos de respuesta
            if create_response.status_code not in [200, 201]:
                print("Error al crear el dataset en Fuseki:", create_response.text)
                return render(request, "upload.html", {
                    "form": form,
                    "error": f"Error al crear el dataset: {create_response.text}"
                })

            print(f"Dataset '{dataset_name}' creado correctamente en Fuseki.")

            # Se suben los datos al dataset recién creado
            dataset_url = f"{URL_FUSEKI}/{dataset_name}/data"
            response = requests.post(
                dataset_url,
                data=rdf_data,
                headers={
                    "Content-Type": mime_type,
                    "Accept": "application/json"
                }
            )

            # Códigos de respuesta
            if response.status_code in [200, 201]:
                return redirect("index")
            else:
                print("Error en Fuseki al subir datos:", response.status_code, response.text)
                return render(request, "upload.html", {
                    "form": form,
                    "error": f"Error en Fuseki: {response.text}"
                })

    else:
        form = RDFUploadForm()
    return render(request, "upload.html", {"form": form})


# ---
# Vista para el Dashboard/Index
def index(request): 
    # Se obtienen los datasets. Si no hay, se redirige a la página de subida
    datasets = obtener_datasets()
    if not datasets: return redirect("subida")
    
    # Se comprueba si hay un dataset seleccionado en la URL para cargarlo
    selected_dataset = request.GET.get("dataset")
    # Si no lo hay, se selecciona el primero de la lista y se construye la url
    if not selected_dataset:
        first_dataset = datasets[0]
        return redirect(f"{request.path}?dataset={first_dataset}")
    
    # Formulario con datasets disponibles
    form = DatasetSelectionForm(request.GET, datasets=datasets)
    
    # SPARQLQuery genera el endpoint, pero hay que pasarle el nombre del dataset
    sparql = SPARQLQuery(selected_dataset)

    # Consultas SPARQL para extraer estadísticas
    queries = {
        "num_tripletas": "SELECT (COUNT(*) AS ?numero) WHERE { ?s ?p ?o }",
        "num_clases": "SELECT (COUNT(DISTINCT ?class) AS ?numero) WHERE { ?s a ?class }",
        "num_instancias": "SELECT (COUNT(DISTINCT ?s) AS ?numero) WHERE { ?s a ?type }",
        "num_propiedades": "SELECT (COUNT(DISTINCT ?p) AS ?numero) WHERE { ?s ?p ?o }",
        "clases": """SELECT 
                        (SAMPLE(REPLACE(STR(?class), "^.*[#/]", "")) AS ?label)
                        (COUNT(?s) AS ?count)
                    WHERE { ?s a ?class } 
                    GROUP BY ?class
                    ORDER BY DESC(?count)
                """,  #Las clases y el número de veces que aparecen. Se intenta recuperar la última parte de la URL siempre que se pueda (se intenta partir por # y /)
        "propiedades": """SELECT 
                            (SAMPLE(REPLACE(STR(?p), "^.*[#/]", "")) AS ?label)
                            (COUNT(?s) AS ?count)
                        WHERE { ?s ?p ?o } 
                        GROUP BY ?p
                        ORDER BY DESC(?count)
                    """, #Propiedades y num de veces
        "propiedades_clases": """SELECT 
                                    (SAMPLE(REPLACE(STR(?s_class), "^.*[#/]", "")) AS ?s_class_label)
                                    (SAMPLE(REPLACE(STR(?p), "^.*[#/]", "")) AS ?p_label)
                                    (COUNT(*) AS ?count)
                                WHERE { 
                                    ?s ?p ?o .
                                    ?s a ?s_class .
                                } 
                                GROUP BY ?s_class ?p
                        """,# Veces que cada propiedad aparece en cada clase
        "relaciones_clases": """SELECT 
                                    (SAMPLE(REPLACE(STR(?clase_origen), "^.*[#/]", "")) AS ?clase_origen_label)
                                    (SAMPLE(REPLACE(STR(?clase_destino), "^.*[#/]", "")) AS ?clase_destino_label)
                                    (COUNT(*) AS ?count)
                                WHERE { 
                                    ?instancia_origen a ?clase_origen .
                                    ?instancia_destino a ?clase_destino .
                                    ?instancia_origen ?p ?instancia_destino .
                                } 
                                GROUP BY ?clase_origen ?clase_destino
                                ORDER BY DESC(?count)
                            """ # Número de veces que se relaciona cada clase a través de sus instancias
    } 
    # Ejecutar consultas y obtener resultados
    try:
        # Ejecuta las consultas que empiezan por num_, ya que son las estadísticas generales del dataset
        stats = {}
        for key, q in queries.items():
            if key.startswith("num_"):
                resultado = sparql.ejecutar_consulta(q)
                stats[key] = int(resultado["results"]["bindings"][0]["numero"]["value"])
                
        # Clases
        resultado_clases = sparql.ejecutar_consulta(queries["clases"])
        clases = [(res["label"]["value"], int(res["count"]["value"])) for res in resultado_clases["results"]["bindings"]]

        # Propiedades
        resultado_propiedades = sparql.ejecutar_consulta(queries["propiedades"])
        propiedades = [(res["label"]["value"], int(res["count"]["value"])) for res in resultado_propiedades["results"]["bindings"]]

        # Relaciones de propiedades y clases
        resultado_propiedades_clases = sparql.ejecutar_consulta(queries["propiedades_clases"])
        propiedades_clases = [(res["s_class_label"]["value"], res["p_label"]["value"], int(res["count"]["value"])) for res in resultado_propiedades_clases["results"]["bindings"]]
        
        # Relaciones entre clases
        resultado_relaciones_clases = sparql.ejecutar_consulta(queries["relaciones_clases"])
        relaciones_clases = [(res["clase_origen_label"]["value"], res["clase_destino_label"]["value"], int(res["count"]["value"])) for res in resultado_relaciones_clases["results"]["bindings"]]

        # Renderizar la página con los datos obtenidos
        return render(request, "index.html", {
            "form": form,
            "datasets": datasets,
            "dataset": selected_dataset,
            "num_tripletas": stats.get("num_tripletas", 0),
            "num_clases": stats.get("num_clases", 0),
            "num_instancias": stats.get("num_instancias", 0),
            "num_propiedades": stats.get("num_propiedades", 0),
            "clases_json": json.dumps(clases),
            "propiedades_json": json.dumps(propiedades),
            "propiedades_clases_json": json.dumps(propiedades_clases),
            "relaciones_clases_json": json.dumps(relaciones_clases),
        })
    # Error
    except Exception as e:
        return render(request, "index.html", {"error": f"Error al recuperar los datos RDF: {str(e)}"})


# --
# Vista de la información de cada clase
def explorar_clase(request, clase):

    selected_dataset = request.GET.get("dataset")
    if not selected_dataset:
        return render(request, "explorar_clase.html", {"clase": clase, "propiedades": [], "instancias": []})

    sparql = SPARQLQuery(selected_dataset)

    # Se obtiene la URI de la clase para poder recuperar datos sobre esta
    query_uri_clase = f"""
        SELECT DISTINCT ?class_uri WHERE {{
            ?s a ?class_uri .
            FILTER(CONTAINS(STR(?class_uri), "{clase}"))  
        }}
    """
    # Se ejecuta consulta
    resultado_clase_uri = sparql.ejecutar_consulta(query_uri_clase)
    # Si no se encuentra la URI de la clase, devolver vacío
    if not resultado_clase_uri["results"]["bindings"]:
        return render(request, "explorar_clase.html", {
            "clase": clase, "propiedades": [], "instancias": [], "dataset": selected_dataset})
    # Extraemos la URI real de la clase
    uri_real_clase = resultado_clase_uri["results"]["bindings"][0]["class_uri"]["value"]
    
    
    # Consulta SPARQL para obtener las propiedades utilizadas por la clase con su label, si lo tiene
    query_propiedades = f"""
        SELECT DISTINCT ?propiedad  (COUNT(?propiedad) AS ?num_propiedad) WHERE {{
            ?s a <{uri_real_clase}> ;
               ?propiedad ?o .
        }} GROUP BY ?propiedad ORDER BY DESC (?num_propiedad)
    """

    # Consulta para obtener el número total de instancias de la clase
    query_num_instancias = f"""
        SELECT (COUNT(?instancia) AS ?total_instancias) WHERE {{
            ?instancia a <{uri_real_clase}> .
        }}
    """
    
    # Consulta SPARQL para obtener un listado de instancias de la clase con el label
    query_instancias = f"""
        SELECT DISTINCT ?instancia ?label WHERE {{
            ?instancia a <{uri_real_clase}> .
            
            OPTIONAL {{ 
                ?instancia ?anyPredicate ?label .
                FILTER(REGEX(STR(?anyPredicate), "label", "i"))  
            }}
        }}
    """

    # Ejecutamos las consultas
    resultado_propiedades = sparql.ejecutar_consulta(query_propiedades)
    resultado_num_instancias = sparql.ejecutar_consulta(query_num_instancias)
    resultado_instancias = sparql.ejecutar_consulta(query_instancias)

    # Procesamos las propiedades
    propiedades = {obtener_nombre_uri(res["propiedad"]["value"]): res["num_propiedad"]["value"]
                   for res in resultado_propiedades["results"]["bindings"]}
    
    # Num instancias
    num_instancias_totales = resultado_num_instancias["results"]["bindings"][0]["total_instancias"]["value"] if resultado_num_instancias["results"]["bindings"] else "0"
    
    # Procesamos las instancias. Misma lógica
    instancias = []
    for res in resultado_instancias["results"]["bindings"]:
        label = res.get("label", {}).get("value", "").strip()  # Obtener label si existe
        uri = res["instancia"]["value"]  # URI de la instancia
        
        nombre_mostrado = label if label else obtener_nombre_uri(uri)  # Si hay label, se usa; si no, se extrae el nombre de la URI
        
        # Se añade tanto la uri de la instancia para posteriormente visualizar sus datos, como el nombre mostrado
        instancias.append({"uri": uri, "nombre": nombre_mostrado}) 

    # Paginación de instancias
    paginator = Paginator(instancias, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    return render(request, "explorar_clase.html", {
        "clase": clase,
        "propiedades": propiedades,
        "instancias": page_obj,
        "num_instancias": num_instancias_totales,
        "dataset": selected_dataset
    })


# Visualización de propiedades y valores de cada instancia
def visualizar_instancia(request):
    
    # Se recogen los parámetros de la url
    selected_dataset = request.GET.get("dataset")
    instancia_uri = request.GET.get("uri") # Se selecciona la uri de la instancia para poder hacer las consultas
    instancia_nombre = request.GET.get("nombre")  # Nombre de la instancia
    
    if not selected_dataset or not instancia_uri:
        return render(request, "visualizar_instancia.html", {"instancia": "Desconocida", "detalles": [], "dataset": selected_dataset})

    instancia_uri = urllib.parse.unquote(instancia_uri)  # Decodificamos la URI
    sparql = SPARQLQuery(selected_dataset)

    # Si el nombre de la instancia no se ha pasado en la URL, intentamos obtenerlo con SPARQL
    if not instancia_nombre:
        query_label = f"""
            SELECT DISTINCT ?label WHERE {{
                <{instancia_uri}> ?anyPredicate ?label .
                FILTER(REGEX(STR(?anyPredicate), "label", "i"))
            }}
            LIMIT 1
        """
        resultado_label = sparql.ejecutar_consulta(query_label)

        if resultado_label["results"]["bindings"]:
            instancia_nombre = resultado_label["results"]["bindings"][0]["label"]["value"]
        else:
            # Si no tiene label, se obtiene la última parte de la URI
            instancia_nombre = obtener_nombre_uri(instancia_uri)
            
            
    # Consulta SPARQL para obtener las propiedades y valores de la instancia
    query_detalles = f"""
        SELECT DISTINCT ?propiedad ?valor WHERE {{
            <{instancia_uri}> ?propiedad ?valor . }}
    """
    resultado_detalles = sparql.ejecutar_consulta(query_detalles)

     # Consulta para obtener todas las clases del dataset (para verificar si el valor de una propiedad es una clase)
    query_clases = """
        SELECT DISTINCT ?class WHERE { ?s a ?class . }
    """
    resultado_clases = sparql.ejecutar_consulta(query_clases)
    clases_existentes = {res["class"]["value"] for res in resultado_clases["results"]["bindings"]}  # Convertimos en conjunto


    # Procesamos los datos
    detalles = []
    for res in resultado_detalles["results"]["bindings"]:
        # Se obtiene la propiedad y se procesa la uri para que sea legible
        propiedad_uri = res["propiedad"]["value"]
        propiedad_nombre = obtener_nombre_uri(propiedad_uri)
        valor_uri = res["valor"]["value"]

        # Verificar si el valor de una propiedad es una URI para visualizarla correctamente
        if valor_uri.startswith("http"):
             # Intentar obtener el label del valor
            query_label_valor = f"""
                SELECT DISTINCT ?label WHERE {{
                    <{valor_uri}> ?anyPredicate ?label .
                    FILTER(REGEX(STR(?anyPredicate), "label", "i"))
                }}
                LIMIT 1
            """
            resultado_label_valor = sparql.ejecutar_consulta(query_label_valor)
            
            if resultado_label_valor["results"]["bindings"]:
                valor_nombre = resultado_label_valor["results"]["bindings"][0]["label"]["value"]
            else:
                valor_nombre = obtener_nombre_uri(valor_uri)  # Si no hay label, usar la última parte de la URI
            
            if valor_uri in clases_existentes:  # Si el valor es una clase, enlazar a la exploración de clase
                valor_enlace = f"/consulta_visualizacion/explorar/{urllib.parse.quote(obtener_nombre_uri(valor_uri))}?dataset={selected_dataset}"
                detalles.append((propiedad_nombre, valor_nombre, valor_enlace, "clase"))
            else:  # Si no es clase, verificar si es una instancia del dataset
                query_check_instance = f"ASK {{ <{valor_uri}> ?p ?o . }}"
                es_instancia = sparql.ejecutar_consulta(query_check_instance)["boolean"]

                if es_instancia:  # Si es instancia, enlazar a la página de instancia
                    valor_enlace = f"/consulta_visualizacion/instancia/?dataset={selected_dataset}&uri={urllib.parse.quote(valor_uri)}"
                    detalles.append((propiedad_nombre, valor_nombre, valor_enlace, "instancia"))
                else:  # Si no es ni clase ni instancia, es un enlace externo
                    detalles.append((propiedad_nombre, valor_nombre, valor_uri, "externo"))
        else:  # Si el valor no es una URI, mostrarlo como texto normal
            detalles.append((propiedad_nombre, valor_uri, None, "dato"))

    return render(request, "visualizar_instancia.html", {
        "instancia": instancia_uri,
        "instancia_nombre": instancia_nombre,
        "detalles": detalles,
        "dataset": selected_dataset
    })

# ---
# Vista para manejar consultas
def consulta_sparql(request):
    selected_dataset = request.GET.get("dataset")
    # Se inicializan variables 
    query_result = None
    error_message = None
    resultados = []  
    page_obj = None  
    consulta_realizada = False  # Para mostrar o no mensaje sobre no resultados
    num_resultados = 0 

    # Si el usuario ha enviado una nueva consulta (POST) se guarda en la sesión y se redirige a la página 1
    if request.method == "POST":
        consulta = request.POST.get("consulta_sparql", "").strip()
        if consulta:  # Evitar guardar consultas vacías
            request.session["ultima_consulta"] = consulta  # Guardar la consulta en la sesión
            consulta_realizada = True
            return redirect(f"{request.path}?dataset={selected_dataset}&page=1")  # Redirigir a la primera página
        else:
            request.session.pop("ultima_consulta", None)  # Eliminar si no hay consulta
    # Si el usuario está navegando entre páginas (GET con ?page), recuperar la consulta de la sesión
    elif "page" in request.GET and "ultima_consulta" in request.session:
        consulta = request.session["ultima_consulta"]
        consulta_realizada = True
    else:
        consulta = ""  # Si no hay consulta en POST ni en sesión, establecer una cadena vacía

    # Si hay consulta, se intenta ejecutar. Si no hay resultados o hay un error, se deja la lista vacía
    if selected_dataset and consulta:
        sparql = SPARQLQuery(selected_dataset)
        try:
            query_result = sparql.ejecutar_consulta(consulta)
            resultados = query_result.get("results", {}).get("bindings", [])  # Si no hay resultados, devolvemos una lista vacía
            num_resultados = len(resultados) #Contar el número de resultados obtenidos
        except Exception as e:
            error_message = f"Error al ejecutar la consulta: {str(e)}"
            resultados = []  # En caso de error, se deja la lista vacía

    # Paginación
    paginator = Paginator(resultados, 10)
    page_number = request.GET.get("page")
    try:
        page_obj = paginator.get_page(page_number)
    except (PageNotAnInteger, EmptyPage):
        page_obj = paginator.get_page(1)  # Si la página no es válida, redirigir a la primera

    return render(request, "consulta_sparql.html", {
        "query_result": query_result,
        "page_obj": page_obj,
        "error_message": error_message,
        "dataset": selected_dataset,
        "consulta_realizada": consulta_realizada,  
        "ultima_consulta": consulta,  # Se pasa la consulta a la plantilla para mantenerla en el textarea
        "num_resultados": num_resultados
    })

