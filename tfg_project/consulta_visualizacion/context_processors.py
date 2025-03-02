from .utils import cargar_json_dataset 

# Context processor para pasar las clases a las plantillas.
# Se cargan desde el JSON generado para mejorar el rendimiento.
def clases(request):
    selected_dataset = request.GET.get("dataset")
    
    # Si no hay dataset seleccionado, devolvemos un diccionario vacío
    if not selected_dataset:
        return {"clases_json": {}}

    # Cargar los datos del JSON
    dataset_data = cargar_json_dataset(selected_dataset)
    
    # Si dataset_data es None, asignar un diccionario vacío
    if dataset_data is None:
        dataset_data = {}

    # Extraer clases del JSON si existen
    clases = dataset_data.get("clases", {})  # Diccionario {label: URI}
    
    return {"clases_json": clases}


