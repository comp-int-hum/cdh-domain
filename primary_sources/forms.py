from cdh import settings
from django import forms
from django.forms import FileField
from django.core.exceptions import ValidationError
from django_registration.forms import RegistrationFormUniqueEmail
from . import models
if settings.USE_LDAP:
    import ldap
    from ldap import modlist

class AddDatasetForm(forms.ModelForm):
    class Meta:
        model = models.Dataset
        fields = ["name"]

class DatasetForm(forms.ModelForm):
    schema_file = FileField(label='An OWL file describing the domain', required=False)
    data_file = FileField(label='An RDF file of primary sources matching the domain', required=False)
    annotation_file = FileField(label='An RDF file of annotations pointing into the primary sources', required=False)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    class Meta:
        model = models.Dataset
        fields = "__all__" #["name", "schema_file", "annotation_file", "data_file", "owned_by"]
