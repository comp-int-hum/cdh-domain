# from cdh import settings
# from django import forms
# from django.forms import FileField, JSONField, CharField
# from django.core.exceptions import ValidationError
# #from django_registration.forms import RegistrationFormUniqueEmail
# from django.shortcuts import render
# from django.template.response import SimpleTemplateResponse
# from django.forms import ModelForm, modelform_factory, FileField
# #from guardian.shortcuts import get_objects_for_user
# #from cdh import widgets
# from cdh.widgets import VegaWidget, MonacoEditorWidget
# from .models import PrimarySource
# from .vega import PrimarySourceSchemaGraph

# from . import models
# #if settings.USE_LDAP:
# #    import ldap
# #    from ldap import modlist


# # class QueryForm(forms.ModelForm):
# #     def __init__(self, *args, user=None, **kwargs):
# #         super().__init__(*args, **kwargs)
# #     class Meta:
# #         model = models.Query
# #         fields = ["name", "sparql"]
# #         widgets = {
# #             "sparql" : MonacoEditorWidget(language="sparql", content_field="sparql", default_value="""SELECT ?d ?p ?r
# # WHERE {
# # ?d ?p ?r .
# # } limit 10
# # """
# #             )
# #         }


# class PrimarySourceViewForm(ModelForm):
#     schema = CharField(widget=VegaWidget(vega_class=PrimarySourceSchemaGraph), label="")

#     def __init__(self, *argv, **argd):
#         self.instance = argd["instance"]
#         super(PrimarySourceViewForm, self).__init__(*argv, **argd)
    
#     def __str__(self):
#         return VegaWidget(vega_class=PrimarySourceSchemaGraph).render("", getattr(self.instance, "vega_triples"))
    
#     class Meta:        
#         model = PrimarySource
#         fields = ('schema',)


# class PrimarySourceEditForm(ModelForm):    
#     schema = CharField(widget=MonacoEditorWidget(language="json"), label="")

#     def __init__(self, *argv, **argd):
#         if argd["instance"]:
#             argd["initial"] = {} if argd.get("initial", None) == None else argd["initial"]
#             argd["initial"]["schema"] = argd["instance"].schema            
#         super(PrimarySourceEditForm, self).__init__(*argv, **argd)
    
#     class Meta:        
#         model = PrimarySource
#         fields = ('schema',)

        
# class PrimarySourceCreateForm(ModelForm):
#     schema_file = FileField()
#     data_file = FileField()
#     annotation_file = FileField()
#     materials_file = FileField()

#     def __init__(self, *argv, **argd):
#         super(PrimarySourceCreateForm, self).__init__(*argv, **argd)
    
#     class Meta:        
#         model = PrimarySource
#         fields = ["name", "schema_file", "data_file", "annotation_file", "materials_file"]
    
