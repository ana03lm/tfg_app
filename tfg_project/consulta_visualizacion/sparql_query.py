from SPARQLWrapper import SPARQLWrapper, JSON

# Clase para manejar las consultas SPARQL
class SPARQLQuery:
    def __init__(self, dataset): #Se pasa el parámetro del dataset para saber cuál es el endpoint
        self.endpoint = f"http://localhost:3030/{dataset}/sparql"
        self.sparql = SPARQLWrapper(self.endpoint)

    def ejecutar_consulta(self, query):
        self.sparql.setQuery(query)
        self.sparql.setReturnFormat(JSON)
        return self.sparql.query().convert()

