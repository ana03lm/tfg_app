from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def get_value(dictionary, key):
    # Extrae el valor de una clave dentro de la estructura JSON de resultados SPARQL
    # Si el valor es una URL, devuelve un enlace HTML
    valor = dictionary.get(key, {}).get("value", "N/A")

    # Si es una URL, la convierte en un enlace clickeable
    if isinstance(valor, str) and re.match(r'^https?://', valor):
        return mark_safe(f'<a href="{valor}" target="_blank">{valor}</a>')

    return valor
