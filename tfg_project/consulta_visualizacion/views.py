from .sparql_query import SPARQLQuery 
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import os
import urllib.parse
import requests
import json
import csv
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

            # Códigos de respuesta 
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
# Vista para eliminar el dataset seleccionado de FUSEKI
def eliminar_dataset(request):
    if request.method == "POST":
        dataset_seleccionado = request.POST.get("dataset")
        if dataset_seleccionado:
            url = f"{URL_FUSEKI}/$/datasets/{dataset_seleccionado}"
            try:
                # Eliminar el JSON relacionado si existe
                json_path = os.path.join("json_cache", f"{dataset_seleccionado}.json")
                if os.path.exists(json_path):
                    os.remove(json_path) 
                
                # Se elimina el dataset
                response = requests.delete(url)
                
                # Si funciona, se redirige a index
                if response.status_code in [200, 204]:
                    return redirect("index") 
                
                else:
                    # Si hay error, se muestra un mensaje en la plantilla
                    error_msg = f"Error al eliminar el dataset: {response.status_code} {response.text}"
                    return render(request, "index.html", {"error": error_msg})
            except Exception as e:
                return render(request, "index.html", {"error": str(e)})

    return redirect("index")

# ---
# Vista para cargar el dataset
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
    
    return render(request, "index.html", {
        "form": form,
        "datasets": datasets,
        "dataset": selected_dataset,
    })


# ---
# GESTIÓN DEL JSON
# Función para generar JSON en segundo plano e imprimir mensajes de progreso
def generar_json_en_segundo_plano(dataset):
    # Ruta del archivo de estado
    estado_path = os.path.join("json_cache", f"{dataset}_generando.json")

    # Función para escribir mensajes en el archivo de estado
    def actualizar_estado(mensaje):
        with open(estado_path, "w") as f:
            f.write(mensaje)

    # Crear archivo con el mensaje inicial
    actualizar_estado("Iniciando la generación del dataset...")

    # Generar el JSON, que utiliza la función actualizar_estado para imprimir mensajes en cada paso
    try:
        actualizar_estado("Obteniendo métricas generales...")
        utils.generar_json_dataset(dataset, actualizar_estado)
        # Si la generación del JSON termina con éxito, se actualiza el estado a "Generación completada"
        actualizar_estado("Generación completada.")
    except Exception as e:
        # Si ocurre un error durante la generación del JSON, el archivo de estado se actualiza con el mensaje de error
        # Esto permite mostrar el error en la pantalla en lugar de esperar indefinidamente
        actualizar_estado(f"Error en la generación: {str(e)}")

    # Eliminar archivo de estado cuando termine
    if os.path.exists(estado_path):
        os.remove(estado_path)

# Vista para mostrar pantalla de carga mientras que se genera JSON
def vista_generar_json(request):
    # Se obtiene el dataset cuyo JSON hay que generar
    selected_dataset = request.GET.get("dataset") or request.POST.get("dataset")

    if selected_dataset:
        # Eliminar el JSON anterior antes de generar uno nuevo
        json_path = os.path.join("json_cache", f"{selected_dataset}.json")
        if os.path.exists(json_path):
            os.remove(json_path)  # Borra el JSON anterior para forzar la generación de uno nuevo, para cuando se pulse el botón de actualizar
            
        # Inicia la generación en un hilo separado
        thread = threading.Thread(target=generar_json_en_segundo_plano, args=(selected_dataset,))
        thread.start()

        # Muestra la pantalla de carga mientras se genera el JSON
        return render(request, "creando_json.html", {"dataset": selected_dataset})

    return redirect("index")  # Si no hay dataset, redirige al inicio

# Comprueba el estado de la generación del JSON del dataset y devuelve el estado actual para controlar la pantalla de carga y los mensajes de progreso
def verificar_json(request):
    # Obtiene el dataset que se procesa 
    selected_dataset = request.GET.get("dataset")
    if not selected_dataset:
        return JsonResponse({"exists": False, "generating": False})

    json_path = os.path.join("json_cache", f"{selected_dataset}.json") #Ruta del archivo JSON del dataset
    estado_path = os.path.join("json_cache", f"{selected_dataset}_generando.json") #Ruta del archivo de estado sobre la generación del JSON anterior

    # Comprueba si existen los archivos anteriores para detectar si ha finalizado el proceso o no y redirigir a index
    json_existe = os.path.exists(json_path)
    json_generando = os.path.exists(estado_path) 

    # Obtiene el mensaje de progreso
    progreso = "Generando datos..." #Mensaje por defecto
    # Si el archivo de estado existe, se lee su contenido y se usa como el mensaje real de progreso
    if json_generando:
        with open(estado_path, "r") as f:
            progreso = f.read().strip()

    # Devuelve un JSON con el estado y el progreso 
    return JsonResponse({"exists": json_existe, "generating": json_generando, "progress": progreso})


# ---
# Vista para explorar el dataset con dashboard o mediante filtrado
def estadisticas (request):
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

    sparql = SPARQLQuery(selected_dataset)
    # Comprobar si el usuario ha realizado una búsqueda (al menos un filtro no está vacío)
    busqueda_realizada = False
    
    # Obtener filtros desde la URL
    clase_base = request.GET.get('clase_base', 'todas').strip()
    filtro_clase = request.GET.get("filtro_clase", "").strip()
    filtro_sujeto = request.GET.get("filtro_sujeto", "").strip()
    filtro_propiedad = request.GET.get("filtro_propiedad", "").strip()
    filtro_objeto = request.GET.get("filtro_objeto", "").strip()
    modo_filtro = request.GET.get("modo_filtro", "AND")  # Por defecto AND
    
    # Obtener datos del JSON
    dataset_data = utils.cargar_json_dataset(selected_dataset)
    clases_dict = dataset_data.get("clases", {}) if dataset_data else {}
    propiedades_dict = dataset_data.get("propiedades", {}) if dataset_data else {}
     
    #  Si hay algún filtro, entonces busqueda_realizada es True
    if clase_base != "todas" or any([filtro_clase, filtro_sujeto, filtro_propiedad, filtro_objeto]):
        busqueda_realizada = True
    
    # Si se ha realizado una búsqueda, se realiza la consulta y se procesan los resultados
    if busqueda_realizada:
        instancias = []
        
        # Si se ha seleccionado clase base, se obtienen los resultados de esta
        # También se obtienen las propiedades para que en el select solo figuren las que son utilizadas por la clase base
        if clase_base != "todas":
            
            # Se obtiene la uri de la clase  base
            uri_real_clase = clases_dict.get(clase_base, None)
                        
            # Generar la consulta SPARQL a partir de los parámetros 
            query_instancias = utils.busqueda( filtro_clase, filtro_sujeto, filtro_propiedad, filtro_objeto, modo_filtro, clases_dict, uri_real_clase )

            # Consulta SPARQL para obtener las propiedades utilizadas por la clase y su frecuencia de uso
            query_propiedades = f"""
                SELECT DISTINCT ?propiedad (COUNT(?propiedad) AS ?num_propiedad) WHERE {{
                    ?s a <{uri_real_clase}> ;
                    ?propiedad ?o .
                }} GROUP BY ?propiedad ORDER BY DESC (?num_propiedad)
            """
            
           # Ejecutamos las consultas
            resultado_propiedades = sparql.ejecutar_consulta(query_propiedades)
            # Procesamos las propiedades para el select
            propiedades_dict = {utils.obtener_nombre_uri(res["propiedad"]["value"]): res["num_propiedad"]["value"]
                        for res in resultado_propiedades["results"]["bindings"]}
        else:
            # Si no se ha elegido clase base, entonces se utilizan el resto de filtros para formar la consulta
            query_instancias = utils.busqueda(filtro_clase, filtro_sujeto, filtro_propiedad, filtro_objeto, modo_filtro, clases_dict)
           
        # Ejecutar la consulta
        resultado_instancias = sparql.ejecutar_consulta(query_instancias)
        # Procesamos las instancias y generamos un diccionario con uri y label para cada una
        for res in resultado_instancias["results"]["bindings"]:
            label = res.get("label", {}).get("value", "").strip()  # Obtener label si existe
            uri = res["s"]["value"]  # URI de la instancia
            nombre_mostrado = label if label else utils.obtener_nombre_uri(uri)  # Si hay label, se usa; si no, se extrae el nombre de la URI
            instancias.append({"uri": uri, "nombre": nombre_mostrado})

        # Contar el total de instancias obtenidas
        num_instancias = len(instancias) 
    
        # Paginación (20 por página)
        paginator = Paginator(instancias, 20)  # Número de elementos por página
        page_number = request.GET.get("page", 1)
        try:
            page_obj = paginator.get_page(page_number)
        except (PageNotAnInteger, EmptyPage):
            page_obj = paginator.get_page(1)  # Si la página no es válida, redirigir a la primera
        
        # Se devuelven los datos necesarios para generar la vista filtrado_instancias
        return render(request, "filtrado_instancias.html", {
            "dataset": selected_dataset,
            "busqueda_realizada": busqueda_realizada,  # Para controlar si se muestran instancias o no
            # Mostrar instancias
            "instancias": page_obj,
            "num_instancias": num_instancias,
            # Se pasan los filtros para mantenerlos en la plantilla
            "clase_base": clase_base,
            "filtro_clase": filtro_clase,
            "filtro_sujeto": filtro_sujeto,
            "filtro_propiedad": filtro_propiedad,
            "filtro_objeto": filtro_objeto,
            "modo_filtro": modo_filtro,
            # Se pasan las clases y propiedades del dataset para los select
            "clases_disponibles": list(clases_dict.keys()),
            "propiedades_disponibles": propiedades_dict,
        })
    else:
        # Si no hay una busqueda, entonces se muestra el dashboard con las visualizaciones
        return render(request, "dashboard.html", {
        "dataset": selected_dataset,
        "busqueda_realizada": busqueda_realizada,  # Para controlar si se muestran instancias o no
        # Datos para enerar visualizaciones
        "num_tripletas": dataset_data.get("num_tripletas", 0),
        "num_clases": dataset_data.get("num_clases", 0),
        "num_instancias": dataset_data.get("num_instancias", 0),
        "num_propiedades": dataset_data.get("num_propiedades", 0),
        "distribucion_clases": json.dumps(dataset_data.get("distribucion_clases", [])),
        "distribucion_propiedades": json.dumps(dataset_data.get("distribucion_propiedades", [])),
        "relacion_propiedades_clases": json.dumps(dataset_data.get("relacion_propiedades_clases", [])),
        "relacion_instancias_clases": json.dumps(dataset_data.get("relacion_instancias_clases", [])),
        # Se pasan los filtros para mantenerlos en la plantilla
        "clase_base": clase_base,
        "filtro_clase": filtro_clase,
        "filtro_sujeto": filtro_sujeto,
        "filtro_propiedad": filtro_propiedad,
        "filtro_objeto": filtro_objeto,
        "modo_filtro": modo_filtro,
        # Se pasan las clases y propiedades del dataset para el filtrado
        "clases_disponibles": list(clases_dict.keys()),
        "propiedades_disponibles": sorted(list(propiedades_dict.keys())),
    })

# Exportación de resultados de filtrado a formato .ttl
def exportar_filtrado_ttl(request):
    # Obtener dataset
    dataset = request.GET.get("dataset")
    if not dataset:
        return HttpResponse("Dataset no especificado", status=400)

    # Obtener filtros desde la URL
    clase_base = request.GET.get('clase_base', 'todas').strip()
    filtro_clase = request.GET.get("filtro_clase", "").strip()
    filtro_sujeto = request.GET.get("filtro_sujeto", "").strip()
    filtro_propiedad = request.GET.get("filtro_propiedad", "").strip()
    filtro_objeto = request.GET.get("filtro_objeto", "").strip()
    modo_filtro = request.GET.get("modo_filtro", "AND")

    # Obtener clases
    dataset_data = utils.cargar_json_dataset(dataset)
    clases_dict = dataset_data.get("clases", {}) if dataset_data else {}
    uri_real_clase = clases_dict.get(clase_base, None) if clase_base != "todas" else None

    # Construir consulta SELECT con filtros
    query_select = utils.busqueda(filtro_clase, filtro_sujeto, filtro_propiedad, filtro_objeto, modo_filtro, clases_dict, uri_real_clase)
    sparql = SPARQLQuery(dataset)
    resultado = sparql.ejecutar_consulta(query_select)

    # Extraer URIs de las instancias
    uris = [binding["s"]["value"] for binding in resultado["results"]["bindings"]]

    # Construir consulta DESCRIBE
    describe_query = "DESCRIBE " + " ".join(f"<{uri}>" for uri in uris)

    # Ejecutar consulta DESCRIBE y devolver los resultados en formato Turtle
    sparql.sparql.setQuery(describe_query)
    sparql.sparql.setReturnFormat("turtle")
    resultados_ttl = sparql.sparql.query().convert()
    
    # Permitir la descarga del archivo
    response = HttpResponse(resultados_ttl, content_type="text/turtle")
    response["Content-Disposition"] = 'attachment; filename="resultados_filtrados.ttl"'
    return response

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

    # Recuperar las clases del JSON para visualizar los valores correctamente
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
                valor_enlace = (f"/consulta_visualizacion/estadisticas/?dataset={selected_dataset}"
                f"&clase_base={urllib.parse.quote(valor_nombre)}"
                f"&filtro_clase=&filtro_sujeto=&filtro_propiedad=&filtro_objeto=&modo_filtro=AND")
                
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
    consulta_realizada = False  # Para controlar si se debe mostrar la tabla de resultados
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
    # Si el usuario está navegando entre páginas (GET con ?page), recuperar la consulta de la sesión para mostrarla siempre
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
            
            # Guardar resultados en la sesión para la exportación
            request.session["sparql_resultados"] = resultados
            request.session["sparql_columnas"] = query_result.get("head", {}).get("vars", [])
            request.session["sparql_query"] = consulta
            request.session.modified = True  # Asegurar que Django guarda la sesión
            
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


#  Vista para exportar resultados almacenados en la sesión en el formato seleccionado (CSV, JSON o TSV )
def exportar_resultados_sparql(request):
    
    formato = request.GET.get("formato", "csv").strip()  # Formato de exportación (por defecto, CSV)

    # Recuperar los resultados almacenados en la sesión
    resultados = request.session.get("sparql_resultados")
    columnas = request.session.get("sparql_columnas")
    consulta = request.session.get("sparql_query")

    if not resultados or not consulta:
        return HttpResponse("No hay datos para exportar. Realiza una consulta primero.", status=400)

    # Exportar como CSV
    if formato == "csv":
        # Se crea una respuesta HTTP con el tipo de contenido correspondiente a CSV
        response = HttpResponse(content_type="text/csv") 
        # Se define el encabezado para forzar la descarga del archivo con nombre específico
        response["Content-Disposition"] = 'attachment; filename="consulta_sparql.csv"'
        
        # Se inicializa el escritor CSV que escribirá en la respuesta
        writer = csv.writer(response)
        # Se escribe la primera fila con los nombres de las columnas
        writer.writerow(columnas) 
        # Se recorren los resultados de la consulta y se escriben en el CSV
        for fila in resultados:
            # Para cada fila, se extraen los valores de las columnas y se escriben en el archivo
            writer.writerow([fila.get(var, {}).get("value", "") for var in columnas])
        return response
    
     # Exportar como TSV
    elif formato == "tsv":
        response = HttpResponse(content_type="text/tab-separated-values")
        response["Content-Disposition"] = 'attachment; filename="consulta_sparql.tsv"'

        writer = csv.writer(response, delimiter="\t")  # Se usa tabulación como separador
        writer.writerow(columnas)  # Escribir cabecera
        # Se recorren los resultados de la consulta y se escriben en el TS
        for fila in resultados:
            writer.writerow([fila.get(var, {}).get("value", "") for var in columnas])
            
        return response
    
    # Exportar como JSON
    elif formato == "json":
        response = HttpResponse(content_type="application/json")
        response["Content-Disposition"] = 'attachment; filename="consulta_sparql.json"'

        # Se construye una lista de diccionarios con los datos de cada fila
        json_data = [{var: fila.get(var, {}).get("value", "") for var in columnas} for fila in resultados]
        # Se convierte la lista en un JSON formateado con indentación para mejor legibilidad
        response.write(json.dumps(json_data, indent=4, ensure_ascii=False))  
        
        return response

    return HttpResponse("Formato no soportado.", status=400)