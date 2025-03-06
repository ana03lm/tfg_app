from django import forms

# Formulario de subida de datos
class RDFUploadForm(forms.Form):
    # Solo tiene un campo que es donde se sube el archivo
    rdf_file = forms.FileField(
        label="Subir archivo RDF",
        help_text="Formatos admitidos: .ttl, .rdf, .nt",
        widget=forms.ClearableFileInput(attrs={"accept": ".ttl,.rdf,.nt"}) #Widget que determina los formatos admitidos
    )

# Formulario para elegir dataset de visualización
class DatasetSelectionForm(forms.Form):
    # Desplegable
    dataset = forms.ChoiceField(label="Seleccionar dataset", choices=[], required=True)
    
    def __init__(self, *args, **kwargs):
        datasets = kwargs.pop("datasets", [])
        super().__init__(*args, **kwargs)
        self.fields["dataset"].choices = [(ds, ds) for ds in datasets]  # Carga los datasets disponibles en el desplegable