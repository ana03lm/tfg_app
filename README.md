# Aplicación para la Consulta y Visualiación de Datos Semánticos RDF

Este proyecto es una **aplicación web desarrollada con Django** que permite la **consulta, exploración y visualización de conjuntos de datos RDF** almacenados en Apache Jena Fuseki. Su objetivo es facilitar la comprensión y análisis de grandes datasets semánticos mediante métricas, filtros y visualizaciones interactivas, así como permitir consultas SPARQL avanzadas.

---

## Tecnologías utilizadas

- **Frontend**: Django Templates, HTML5/CSS3, Plotly.js, jQuery
- **Backend**: Django 4.2 (Python)
- **Triplestore**: Apache Jena Fuseki
- **Conexión SPARQL**: SPARQLWrapper

---

## Funcionalidades principales

- Subida de archivos RDF (`.ttl`, `.rdf`, `.nt`)
- Generación automática de estadísticas y dashboard
- Búsqueda de instancias mediante un sistema de filtrado por clase, sujeto, propiedad u objeto
- Visualización detallada de instancias y sus relaciones semánticas
- Editor para consultas SPARQL personalizadas

---

## Instalación y despliegue

### Requisitos previos
Antes de instalar, es necesario tener lo siguiente instalado en tu máquina:
- Python 3.0 o superior
- Django
- Apache Jena Fuseki
- Git
- Pip (gestor de paquetes de Python)
  
### 1. Clonar el repositorio

```bash
git clone https://github.com/ana03lm/tfg_app.git
cd tfg_app.git
````

### 2. Crear un entorno virtual
```bash
python -m venv venv
source venv/bin/activate     # Linux / macOS
.\venv\Scripts\activate      # Windows
```

### 3. Instalar dependencias del proyecto
Ejecuta el siguiente comando para instalar los paquetes:
```bash
pip install django==4.2
pip install SPARQLWrapper==1.8.5
pip install requests
```

### 4. Instalar y ejecutar Apache Jena Fuseki
Ejecuta el siguiente comando para instalar los paquetes:
1. Descarga Fuseki desde: https://jena.apache.org/download/index.cgi
2. Extrae el contenido del ZIP descargado.
3. Accede al directorio y ejecuta el servidor:
```bash
cd apache-jena-fuseki-X.X.X
./fuseki-server    # en Linux / macOS
fuseki-server.bat  # en Windows
```
Esto levanta un servidor en http://localhost:3030. Puedes acceder a través de cualquier navegador para comprobar que se ha ejecutado correctamente.

### 5. Ejecutar la aplicación Django
Finalmente, cuando tienes ya todo instalado, puedes poner en marcha la aplicación con el siguiente comando:
```bash
python manage.py runserver
```
Ahora, puedes acceder desde cualquier navegador a la aplicación a través de esta dirección: http://127.0.0.1:8000

## Cómo utilizar la aplicación
1. Ve a la pestaña "Subida" para cargar un nuevo dataset RDF.
2. Espera a que se genere el archivo JSON con las estadísticas.
3. Accede a "Estadísticas" para visualizar métricas y gráficos.
4. Utiliza el panel lateral para filtrar instancias.
5. Pincha en una instancia para ver sus propiedades.
6. Ve a "Consulta SPARQL" para realizar consultas manuales.
7. Exporta los resultados de búsquedas o consultas si lo deseas.

## Ayuda
Dentro de la aplicación encontrarás una sección de Ayuda accesible desde el menú de navegación, donde se explican todas las funcionalidades y cómo utilizarlas paso a paso.

## Licencia
Este proyecto está disponible bajo la licencia Creative Commons Zero v1.0 Universal (CC0 1.0). Puedes usar, modificar y compartir libremente el código.

## Autoría
Aplicación desarrollada como parte del Trabajo Fin de Grado del Grado en Gestión de la Información y Contenidos Digitales (Universidad de Murcia).
Autora: Ana López Morales
