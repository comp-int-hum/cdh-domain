from cdh import settings
from django import forms
from django.forms import FileField, JSONField, CharField
from django.core.exceptions import ValidationError
from django_registration.forms import RegistrationFormUniqueEmail
from django.shortcuts import render
from django.template.response import SimpleTemplateResponse
from django.forms import ModelForm, modelform_factory, FileField
from guardian.shortcuts import get_objects_for_user
from cdh import widgets
from cdh.widgets import VegaWidget, MonacoEditorWidget
from .models import PrimarySource
from .vega import PrimarySourceSchemaGraph

from . import models
if settings.USE_LDAP:
    import ldap
    from ldap import modlist


class QueryForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        #prefix = kwargs["instance"].id if "instance" in kwargs else "unbound"
        super().__init__(*args, **kwargs)
    class Meta:
        model = models.Query
        exclude = ["dataset"]
        widgets = {
            "sparql" : widgets.MonacoEditorWidget(language="sparql", content_field="sparql", default_value="""SELECT DISTINCT ?parent ?child
WHERE {
  ?child rdfs:subClassOf+ ?parent .
  FILTER (!isBlank(?parent))
}
"""
            )
        }


class PrimarySourceGraphicalForm(ModelForm):
    schema = CharField(widget=VegaWidget(vega_class=PrimarySourceSchemaGraph), label="")

    def __init__(self, *argv, **argd):
        if argd["instance"]:
            argd["initial"]["schema"] = argd["instance"].vega
        super(PrimarySourceGraphicalForm, self).__init__(*argv, **argd)
        
    class Meta:        
        model = PrimarySource
        fields = ('schema',)


class PrimarySourceEditorForm(ModelForm):    
    schema = CharField(widget=MonacoEditorWidget(language="json"), label="")

    def __init__(self, *argv, **argd):
        if argd["instance"]:
            argd["initial"] = argd.get("initial", {})
            argd["initial"]["schema"] = argd["instance"].schema            
        super(PrimarySourceEditorForm, self).__init__(*argv, **argd)
    
    class Meta:        
        model = PrimarySource
        fields = ('schema',)


# class PrimarySourceForm(ModelForm):
#     schema_file = FileField(label='An OWL file describing the domain', required=False)
#     data_file = FileField(label='An RDF file of primary sources matching the domain', required=False)
#     annotation_file = FileField(label='An RDF file of annotations pointing into the primary sources', required=False)
#     static_file = FileField(label='An RDF file of annotations pointing into the primary sources', required=False)
    
#     class Meta:
#         model = PrimarySource
#         fields = ('name', )
