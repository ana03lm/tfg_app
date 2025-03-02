from django import template

register = template.Library()

@register.filter #Registra la función como un filtro de Django
def get_value(dictionary, key):
    #  Extrae el valor de una clave dentro de la estructura JSON de resultados SPARQL. Si no existe, devuelve "N/A".
    return dictionary.get(key, {}).get("value", "N/A")
