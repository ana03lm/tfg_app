from .sparql_query import SPARQLQuery

# Context processor que obtiene la lista de clases del dataset seleccionado y la pasa a todas las plantillas.
# No se puede usar una vista ya que son datos que se van a usar en base_generic y se deben renderizar inderectamente en todas las plantillas
def menu_clases(request):

    # Intentamos obtener el dataset desde la URL
    selected_dataset = request.GET.get("dataset")  
    # Diccionario vacío si no hay dataset
    if not selected_dataset:
        return {"clases": []}  

    sparql = SPARQLQuery(selected_dataset)

    # Consulta SPARQL para obtener los nombres de las clases directamente
    query_clases = """
        SELECT DISTINCT 
            (SAMPLE(REPLACE(STR(?class), "^.*[#/]", "")) AS ?label)
        WHERE { 
            ?s a ?class .
        } 
        GROUP BY ?class
        ORDER BY ?label
    """

    # Ejecutamos la consulta
    resultado_clases = sparql.ejecutar_consulta(query_clases)

    # Extraemos directamente los nombres de las clases de la consulta
    clases = [res["label"]["value"] for res in resultado_clases["results"]["bindings"]]

    # Devuelve un diccionario con los datos, no renderiza una plantilla
    return {"clases": clases}  
