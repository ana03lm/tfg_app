from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('subida', views.upload_rdf, name='subida'),
    path("explorar/<str:clase>/", views.explorar_clase, name="explorar_clase"),
    path('instancia/', views.visualizar_instancia, name='visualizar_instancia'),
    path("consulta/", views.consulta_sparql, name="consulta_sparql"),
#     path("ayuda/", ayuda, name="ayuda"),
    path("vista_generar_json/", views.vista_generar_json, name="vista_generar_json"),
    path("verificar_json/", views.verificar_json, name="verificar_json"),
    path("exportar_sparql/", views.exportar_resultados_sparql, name="exportar_resultados_sparql"),
    path('busqueda/', views.busqueda_natural, name='busqueda_natural'),
]