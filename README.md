![1](https://github.com/user-attachments/assets/ff846bd2-a8e8-4bc3-9371-bf3b354c1f8b)# Aplicación para la Consulta y Visualización de Datos Semánticos RDF

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
> En Windows:
>  ```bash
>  python -m venv venv
>  venv\Scripts\activate
>  ```
>  En Linux/macOS:
> ```bash
> python -m venv venv
> source venv/bin/activate
> ```

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
> En Windows:
> ```bash
> fuseki-server.bat --update --tdb2
> ```
> En Linux/macOS:
> ```bash
> ./fuseki-server --update --tdb2
> ```
Esto iniciará Fuseki en modo escritura y con persistencia de datos.
5. Abre tu navegador y accede a: http://localhost:3030/
Si ves el panel de Fuseki, ¡todo está funcionando correctamente!

### 5. Ejecutar la aplicación Django
Vuelve a la terminal donde clonaste el repositorio (o abre una nueva y ve a la carpeta del proyecto):
```bash
cd ruta/tfg_app
```
Asegúrate de que el entorno virtual esté activado con:
> En Windows:
> ```bash
>   fuseki-server.bat --update --tdb2
>   ```
> En Linux/macOS:
> ```bash
> ./fuseki-server --update --tdb2
> ```
Dirígete a la subcarpeta tfg_project:
```bash
cd tfg_project
```
Ejecuta:
```bash
python manage.py runserver
```
Ahora ya puedes abrir tu navegador y visitar la aplicación en: http://127.0.0.1:8000

---

## Cómo volver a iniciar la aplicación
Cada vez que apagues el ordenador o cierres todo, necesitarás replicar parte del paso 4 y 5 anteriormente explicados para iniciar Apache Jena Fuseki y Django. A continuación se explica paso a paso:
### 1. Apache Jena Fuseki
1. Abre una terminal
2. Navega hasta la carpeta donde tengas Fuseki:
   ```bash
   cd ruta/donde/guardaste/apache-jena-fuseki
   ```
3. Ejecuta:
> En Windows:
>   ```bash
>     fuseki-server.bat --update --tdb2
>   ```
>   En Linux/macOS:
> ```bash
> ./fuseki-server --update --tdb2
> ```

**No cierres esta ventana** mientras uses la aplicación.

### 2. La aplicación Django
1. Abre otra terminal.
2. Navega a la carpeta del proyecto:
   ```bash
   cd ruta/tfg_app
   ```
3. Activa el entorno virtual:
> En Windows:
> ```bash
> venv\Scripts\activate
> ```
> En Linux/macOS:
> ```bash
> source venv/bin/activate
> ```
4. Navega a la subcarpeta tfg_project:
   ```bash
   cd tfg_project
   ```
5. Ejecuta:
   ```bash
   python manage.py runserver
   ```
6. Abre tu navegador y accede a: http://127.0.0.1:8000

--- 

## Cómo utilizar la aplicación
A continuación, se explica cómo acceder y hacer uso de las principales funcionalidades de la aplicación.
### Subida de datasets
Para cargar un nuevo conjunto de datos RDF en la aplicación:
- Dirígete a la página de **Subida de Datos**, cuyo enlace se encuentra en la página de inicio
  ![1](https://github.com/user-attachments/assets/61728f00-fbc9-4f31-92e5-2073a035a122)

- Haz clic en "Seleccionar archivo"
  ![2](https://github.com/user-attachments/assets/6e9e0d8f-a4ad-4eea-b927-b7b126e86e53)

- Elige el archivo RDF de tu dispositivo y haz clic en subir. El sistema procesará el archivo y generará un resumen de los datos

### Selección y visualización de datos
Para explorar un dataset cargado en la plataforma:
- Desde la página principal, selecciona un dataset del desplegable
  ![3](https://github.com/user-attachments/assets/daf74d1d-41b8-4e80-9df4-ecbbb43494ce)

- Accede a la sección de Estadísticas para visualizar métricas y gráficos
  ![4](https://github.com/user-attachments/assets/002f0211-8822-49be-8ad3-80316fe41b9a)

### Filtrado de instancias
Para encontrar información específica dentro de un dataset:
- Accede a la página de Estadísticas
- Usa la barra lateral de filtros para buscar por clase, sujeto, propiedad u objeto
  ![5](https://github.com/user-attachments/assets/df8e594a-4946-442b-90d3-c330c5f9a1f1)

- Aplica filtros adicionales usando los modos AND u OR
- Haz clic en "Buscar" para ver los resultados

#### ¿Qué es la clase base?
La clase base define el conjunto principal de instancias sobre el cual se aplicarán el resto de los filtros. Si seleccionas una clase base, todas las instancias mostradas pertenecerán a esa clase. Luego, puedes aplicar otros filtros adicionales para refinar los resultados, combinándolos mediante AND u OR.
Ejemplo: Si trabajas con un dataset sobre películas y seleccionas "Película" como clase base, todas las instancias mostradas serán películas. Luego, podrías aplicar filtros como "director" o "año de estreno" para reducir aún más la búsqueda. Serán estos otros filtros a los que se aplique el modo de búsqueda seleccionado, pero la clase base se mantiene "fija" a pesar de que se utilice OR.
#### Diferencia entre modos de búsqueda AND y OR:
- **AND:** Se muestran solo las instancias que cumplen con todos los filtros aplicados simultáneamente.
- **OR:** Se muestran las instancias que cumplen al menos uno de los filtros aplicados. Sin embargo, la clase base no se ve afectada por esta condición y sigue actuando como filtro fijo.

### Visualización de instancias
Para obtener detalles sobre una instancia específica:
- Tras aplicar un filtro, haz clic en el nombre de una instancia en la lista de resultados
  ![6](https://github.com/user-attachments/assets/1612bc90-ab73-43e1-83ca-5f6c4e0e3fe8)

- Se mostrará una página con las propiedades y valores de la instancia
  ![7](https://github.com/user-attachments/assets/e42a4899-9ea3-478b-be32-5323e412cae3)

- Si hay enlaces a otras instancias, podrás navegar entre ellas

### Consulta de datos con SPARQL
Si deseas realizar consultas avanzadas sobre los datos RDF:
- Ve a la página de consulta SPARQL
  ![8](https://github.com/user-attachments/assets/5ba99492-fc97-429d-9cd5-fa2e713405ab)

- Introduce tu consulta en el editor
- Haz clic en "Ejecutar Consulta"
- Los resultados se mostrarán en formato tabla y se podrán exportar en CSV, TSV o JSON
  ![9](https://github.com/user-attachments/assets/687f7f35-0dd9-4109-bb8d-dee5c16ac638)


### Eliminación y Actualización de Datasets
Si necesitas actualizar o eliminar un dataset:
- Desde la página principal, selecciona un dataset
- Usa los botones "Actualizar dataset" o "Eliminar dataset"
  ![10](https://github.com/user-attachments/assets/4d52c661-1521-49ae-823f-588bf6b21161)

- Si decides eliminar un dataset, se pedirá confirmación antes de proceder.

---

## Licencia
Este proyecto está disponible bajo la licencia Creative Commons Zero v1.0 Universal (CC0 1.0). Puedes usar, modificar y compartir libremente el código.

## Autoría
Aplicación desarrollada como parte del Trabajo Fin de Grado del Grado en Gestión de la Información y Contenidos Digitales (Universidad de Murcia).
Autora: Ana López Morales
