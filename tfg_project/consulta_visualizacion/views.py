from .sparql_query import SPARQLQuery  # Importamos la clase para consultas SPARQL
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os
import urllib.parse
import requests
import json
import threading
from .forms import RDFUploadForm, DatasetSelectionForm
from consulta_visualizacion import utils

# URL base de Fuseki
URL_FUSEKI = "http://localhost:3030"

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

            # Códigos de respuesta. 
            # Si está todo bien se lleva a la página de generación de json
            if response.status_code in [200, 201]:
                return redirect(reverse("vista_generar_json") + f"?dataset={dataset_name}")
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
    datasets = utils.obtener_datasets()
    if not datasets:
        return redirect("subida")
    
    # Se comprueba si hay un dataset seleccionado en la URL para cargarlo
    selected_dataset = request.GET.get("dataset")
    # Si no lo hay, se redirige al primero en la lista
    if not selected_dataset:
        first_dataset = datasets[0]
        return redirect(f"{request.path}?dataset={first_dataset}")
    
    # Formulario con datasets disponibles para seleccionar el que se carga
    form = DatasetSelectionForm(request.GET, datasets=datasets)
    
    # Cargar JSON si existe, si no, enviarlo a generarlo
    dataset_data = utils.cargar_json_dataset(selected_dataset)
    if not dataset_data:
        return redirect(reverse("vista_generar_json") + f"?dataset={selected_dataset}")

    return render(request, "index.html", {
        "form": form,
        "datasets": datasets,
        "dataset": selected_dataset,
        "num_tripletas": dataset_data.get("num_tripletas", 0),
        "num_clases": dataset_data.get("num_clases", 0),
        "num_instancias": dataset_data.get("num_instancias", 0),
        "num_propiedades": dataset_data.get("num_propiedades", 0),
        "distribucion_clases": json.dumps(dataset_data.get("distribucion_clases", [])),
        "distribucion_propiedades": json.dumps(dataset_data.get("distribucion_propiedades", [])),
        "relacion_propiedades_clases": json.dumps(dataset_data.get("relacion_propiedades_clases", [])),
        "relacion_instancias_clases": json.dumps(dataset_data.get("relacion_instancias_clases", [])),
    })



# ---
# GESTIÓN DEL JSON
# Función para generar JSON en segundo plano
def generar_json_en_segundo_plano(dataset):
    # Se crea un archivo temporal para detectar cuando empieza y acaba la generación
    estado_path = os.path.join("json_cache", f"{dataset}_generando.json")
    with open(estado_path, "w") as f:
        f.write("generando")
    
    # Generar el JSON
    utils.generar_json_dataset(dataset)

    # Eliminar el archivo de estado una vez terminado
    if os.path.exists(estado_path):
        os.remove(estado_path)

# Vista para mostrar pantalla de carga mientras que se genera JSON
def vista_generar_json(request):
    # Se obtiene el dataset cuyo JSON hay que generar
    selected_dataset = request.GET.get("dataset") or request.POST.get("dataset")

    if selected_dataset:
        # Inicia la generación en un hilo separado
        thread = threading.Thread(target=generar_json_en_segundo_plano, args=(selected_dataset,))
        thread.start()

        # Muestra la pantalla de carga mientras se genera el JSON
        return render(request, "creando_json.html", {"dataset": selected_dataset})

    return redirect("index")  # Si no hay dataset, redirige al inicio

# Verificar si existe el JSON de estado o no para controlar la carga y la redirección a index
def verificar_json(request):
    selected_dataset = request.GET.get("dataset")
    if not selected_dataset:
        return JsonResponse({"exists": False, "generating": False})

    json_path = os.path.join("json_cache", f"{selected_dataset}.json")
    estado_path = os.path.join("json_cache", f"{selected_dataset}_generando.json")

    json_existe = os.path.exists(json_path)
    json_generando = os.path.exists(estado_path)

    return JsonResponse({"exists": json_existe, "generating": json_generando})


# ---
# Vista de la información de cada clase
def explorar_clase(request, clase):
    selected_dataset = request.GET.get("dataset")
    if not selected_dataset:
        return render(request, "explorar_clase.html", {"clase": clase, "propiedades": [], "instancias": []})

    sparql = SPARQLQuery(selected_dataset)
    
    # Obtener la correspondencia entre la clase solicitada y la URI del dataset a partir del JSON
    dataset_data = utils.cargar_json_dataset(selected_dataset)
    clases_dict = dataset_data.get("clases", {}) if dataset_data else {}
    uri_real_clase = clases_dict.get(clase, None)
    if not uri_real_clase:
        return render(request, "explorar_clase.html", {"clase": clase, "propiedades": [], "instancias": [], "dataset": selected_dataset})

    # Consulta SPARQL para obtener las propiedades utilizadas por la clase con su label, si lo tiene
    query_propiedades = f"""
        SELECT DISTINCT ?propiedad (COUNT(?propiedad) AS ?num_propiedad) WHERE {{
            ?s a <{uri_real_clase}> ;
               ?propiedad ?o .
        }} GROUP BY ?propiedad ORDER BY DESC (?num_propiedad)
    """

    # Consulta para obtener el número total de instancias de la clase
    query_num_instancias = f"""
        SELECT (COUNT(DISTINCT ?instancia) AS ?total_instancias) WHERE {{
            ?instancia a <{uri_real_clase}> .
        }}
    """

    # Obtener filtros desde la URL
    filtro_clase = request.GET.get("filtro_clase", "").strip()
    filtro_propiedad = request.GET.get("filtro_propiedad", "").strip()
    filtro_valor = request.GET.get("filtro_valor", "").strip()
    
    # Construcción de la consulta SPARQL con filtros
    query_instancias = f"""
        SELECT DISTINCT ?instancia ?label WHERE {{
            ?instancia a <{uri_real_clase}> .
    """
    
    # Aplicar filtro de clase si está definido
    if filtro_clase:
        # Si el usuario pone en el filtro el label de la clase
        if filtro_clase in clases_dict.keys():
            query_instancias += f" ?instancia a <{clases_dict[filtro_clase]}> . "
        # Si el usuario pone en el filtro la URI de la clase
        if filtro_clase in clases_dict.values():
            query_instancias += f" ?instancia a <{filtro_clase}> . "
            
    # Aplicar filtro de propiedad si está definido
    if filtro_propiedad:
        query_instancias += f" OPTIONAL {{ ?instancia <{filtro_propiedad}> ?o . }} "
        
    # Aplicar filtro de valor si está definido
    if filtro_valor:
        query_instancias += f"""
            FILTER EXISTS {{
                ?instancia ?propiedad ?valor .
                FILTER(CONTAINS(LCASE(STR(?valor)), LCASE("{filtro_valor}")))
            }}
        """

    # Añadir búsqueda de labels
    query_instancias += """
        OPTIONAL { 
            ?instancia ?anyPredicate ?label .
            FILTER(REGEX(STR(?anyPredicate), "label", "i"))  
        }
    }
    """

    # Ejecutamos las consultas
    resultado_propiedades = sparql.ejecutar_consulta(query_propiedades)
    resultado_num_instancias = sparql.ejecutar_consulta(query_num_instancias)
    resultado_instancias = sparql.ejecutar_consulta(query_instancias)

    # Procesamos las propiedades
    propiedades = {utils.obtener_nombre_uri(res["propiedad"]["value"]): res["num_propiedad"]["value"]
                   for res in resultado_propiedades["results"]["bindings"]}

    # Num instancias
    num_instancias_totales = resultado_num_instancias["results"]["bindings"][0]["total_instancias"]["value"] if resultado_num_instancias["results"]["bindings"] else "0"

    # Procesamos las instancias
    instancias = []
    for res in resultado_instancias["results"]["bindings"]:
        label = res.get("label", {}).get("value", "").strip()  # Obtener label si existe
        uri = res["instancia"]["value"]  # URI de la instancia
        nombre_mostrado = label if label else utils.obtener_nombre_uri(uri)  # Si hay label, se usa; si no, se extrae el nombre de la URI
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
        "dataset": selected_dataset,
        "filtro_clase": filtro_clase,
        "filtro_propiedad": filtro_propiedad,
        "filtro_valor": filtro_valor
    })


# ---
# Visualización de propiedades y valores de cada instancia
def visualizar_instancia(request):
    # Se recogen los parámetros de la URL
    selected_dataset = request.GET.get("dataset")
    instancia_uri = request.GET.get("uri")  # URI de la instancia para poder hacer las consultas
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
            instancia_nombre = utils.obtener_nombre_uri(instancia_uri)

    # Consulta SPARQL para obtener las propiedades y valores de la instancia
    query_detalles = f"""
        SELECT DISTINCT ?propiedad ?valor WHERE {{
            <{instancia_uri}> ?propiedad ?valor . }}
    """
    resultado_detalles = sparql.ejecutar_consulta(query_detalles)

    # Recuperar las clases del JSON
    dataset_data = utils.cargar_json_dataset(selected_dataset)
    clases_dict = dataset_data.get("clases", {}) if dataset_data else {}

    # Procesamos los datos
    detalles = []
    for res in resultado_detalles["results"]["bindings"]:
        # Se obtiene la propiedad y se procesa la URI para que sea legible
        propiedad_uri = res["propiedad"]["value"]
        propiedad_nombre = utils.obtener_nombre_uri(propiedad_uri) 
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
                valor_nombre = utils.obtener_nombre_uri(valor_uri)  # Si no hay label, usar la última parte de la URI

            # Si el valor es una clase, enlazar a la exploración de clase
            if valor_nombre in clases_dict:
                valor_enlace = f"/consulta_visualizacion/explorar/{urllib.parse.quote(valor_nombre)}?dataset={selected_dataset}"
                detalles.append((propiedad_nombre, valor_nombre, valor_enlace, "clase"))
            else:  
                # Verificar si el valor es una instancia del dataset
                query_check_instance = f"ASK {{ <{valor_uri}> ?p ?o . }}"
                es_instancia = sparql.ejecutar_consulta(query_check_instance)["boolean"]
                # Si lo es, se redirige a la página de la instancia
                if es_instancia:  
                    valor_enlace = f"/consulta_visualizacion/instancia/?dataset={selected_dataset}&uri={urllib.parse.quote(valor_uri)}"
                    detalles.append((propiedad_nombre, valor_nombre, valor_enlace, "instancia"))
                # Si no es instancia ni clase, entonces es un enlace a un recurso externo. 
                # Se enlaza
                else:  
                    detalles.append((propiedad_nombre, valor_nombre, valor_uri, "externo"))
        else:  
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

