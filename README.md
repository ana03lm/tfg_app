# Aplicación para la Consulta y Visualización de Datos Semánticos RDF

Este proyecto es una **aplicación web desarrollada con Django** que permite la **consulta, exploración y visualización de conjuntos de datos RDF** almacenados en Apache Jena Fuseki. Su objetivo es facilitar la comprensión y análisis de grandes datasets semánticos mediante métricas, filtros y visualizaciones interactivas, así como permitir consultas SPARQL avanzadas.

---

## Funcionalidades principales de la aplicación

- Subida de archivos RDF (`.ttl`, `.rdf`, `.nt`)
- Generación automática de estadísticas y dashboard
- Búsqueda de instancias mediante un sistema de filtrado por clase, sujeto, propiedad u objeto
- Visualización detallada de instancias y sus relaciones semánticas
- Editor para consultas SPARQL personalizadas

---

## Tecnologías utilizadas

- **Frontend**: Django Templates, HTML5/CSS3, Plotly.js, jQuery
- **Backend**: Django 4.2 (Python)
- **Triplestore**: Apache Jena Fuseki
- **Conexión SPARQL**: SPARQLWrapper (Python)

---

## Requisitos del sistema
Antes de comenzar, asegúrate de tener instalado lo siguiente en tu ordenador:
- **Python 3.8 o superior (se recomienda 3.12):** https://www.python.org/downloads/
- **Git:** https://git-scm.com/
- **Java 17 o superior:** https://www.oracle.com/es/java/technologies/downloads/
Java es necesario para que funcione Apache Jena Fuseki. En el enlace incluido selecciona la versión 17 o superior, tu sistema operativo y descarga preferiblemente un archivo instalador.

> Puedes comprobar si están instalados abriendo una terminal (o símbolo del sistema) y escribiendo:
>
> ```bash
> python --version
> pip --version
> git --version
> java -version
> ```

---
  
## Instalación y despliegue

### 1. Clonar el repositorio
En primer lugar, abre una terminal y ejecuta: 
```bash
git clone https://github.com/ana03lm/tfg_app.git
cd tfg_app
````
Esto descargará todos los archivos necesarios en tu ordenador.

### 2. Crear un entorno virtual
Posteriormente, es recomendable crear un entorno virtual mediante los siguientes comandos.
- En Windows:
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```
- En Linux/macOS:
  ```bash
  python -m venv venv
  source venv/bin/activate
  ```

### 3. Instalar dependencias del proyecto
Con el entorno virtual activado, instala las bibliotecas necesarias:
```bash
pip install django==4.2
pip install SPARQLWrapper==1.8.5
pip install requests
```

### 4. Descargar e iniciar Apache Jena Fuseki
A continuación, debes desplegar Apache Jena Fuseki, que es donde se van a guardar los conjuntos de datos en la aplicación:
1. Descarga el siguiente archivo: https://dlcdn.apache.org/jena/binaries/apache-jena-fuseki-5.4.0.zip
2. Extrae el archivo `.zip` en una carpeta de tu ordenador.
3. Abre **una nueva terminal** y navega hasta esa carpeta: 
  ```bash
  cd ruta/donde/guardaste/apache-jena-fuseki
  ```
4. Inicia el servidor con el siguiente comando:
- En Windows:
  ```bash
  fuseki-server.bat --update --tdb2
  ```
- En Linux/macOS:
  ```bash
  ./fuseki-server --update --tdb2
  ```
Esto iniciará Fuseki en modo escritura y con persistencia de datos.
5. Abre tu navegador y accede a: http://localhost:3030/
Si ves el panel de Fuseki, ¡todo está funcionando correctamente!

### 5. Ejecutar la aplicación Django
Vuelve a la terminal donde clonaste el repositorio (o abre una nueva y ve a la carpeta del proyecto):
```bash
cd ruta/del/proyecto
```
Dirígete a la subcarpeta tfg_project:
```bash
cd ruta/del/proyecto
```
Asegúrate de que el entorno virtual esté activado y ejecuta:
```bash
python manage.py runserver
```
Ahora ya puedes abrir tu navegador y visitar la aplicación en: http://127.0.0.1:8000

## Cómo volver a iniciar la aplicación
Cada vez que apagues el ordenador o cierres todo, necesitarás replicar parte del paso 4 y 5 anteriormente explicados para iniciar Apache Jena Fuseki y Django. A continuación se explica paso a paso:
### 1. Apache Jena Fuseki
1. Abre una terminal
2. Navega hasta la carpeta donde tengas Fuseki:
   ```bash
   cd ruta/donde/guardaste/apache-jena-fuseki
   ```
3. Ejecuta:
  - En Windows:
    ```bash
    fuseki-server.bat --update --tdb2
    ```
- En Linux/macOS:
  ```bash
  ./fuseki-server --update --tdb2
  ```

**No cierres esta ventana** mientras uses la aplicación.

### 2. La aplicación Django
1. Abre otra terminal.
2. Navega a la carpeta del proyecto:
   ```bash
   cd ruta/tfg_app
   ```
3. Activa el entorno virtual:
  - En Windows:
  ```bash
  venv\Scripts\activate
  ```
- En Linux/macOS:
  ```bash
  source venv/bin/activate
  ```
4. Navega a la subcarpeta tfg_project:
   ```bash
   cd tfg_project
   ```
5. Ejecuta:
   ```bash
   python manage.py runserver
   ```
6. Abre tu navegador y accede a: http://127.0.0.1:8000

## Cómo utilizar la aplicación
1. Ve a la pestaña "Subida" para cargar un nuevo dataset RDF.
2. Espera a que se genere el archivo JSON con las estadísticas.
3. Accede a "Estadísticas" para visualizar métricas y gráficos.
4. Utiliza el panel lateral para filtrar instancias.
5. Pincha en una instancia para ver sus propiedades.
6. Ve a "Consulta SPARQL" para realizar consultas manuales.
7. Exporta los resultados de búsquedas o consultas si lo deseas.

## Ayuda
Dentro de la aplicación encontrarás una sección de **Ayuda** accesible desde el menú de navegación, donde se explican todas las funcionalidades y cómo utilizarlas paso a paso.

## Licencia
Este proyecto está disponible bajo la licencia Creative Commons Zero v1.0 Universal (CC0 1.0). Puedes usar, modificar y compartir libremente el código.

## Autoría
Aplicación desarrollada como parte del Trabajo Fin de Grado del Grado en Gestión de la Información y Contenidos Digitales (Universidad de Murcia).
Autora: Ana López Morales
