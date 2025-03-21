from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('subida', views.upload_rdf, name='subida'),
    path("eliminar_dataset/", views.eliminar_dataset, name="eliminar_dataset"),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
    path('instancia/', views.visualizar_instancia, name='visualizar_instancia'),
    path("consulta/", views.consulta_sparql, name="consulta_sparql"),
    path("vista_generar_json/", views.vista_generar_json, name="vista_generar_json"),
    path("verificar_json/", views.verificar_json, name="verificar_json"),
    path("exportar_sparql/", views.exportar_resultados_sparql, name="exportar_resultados_sparql"),
    path("exportar_filtrado_ttl/", views.exportar_filtrado_ttl, name="exportar_filtrado_ttl"),
    path("ayuda/", TemplateView.as_view(template_name="ayuda.html"), name="ayuda"),
]