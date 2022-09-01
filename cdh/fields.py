from django.contrib.gis.db import models
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from .widgets import MonacoEditorWidget
import markdown
from wiki.editors.base import BaseEditor
from rdflib.plugins.sparql import prepareQuery
import json


class MarkdownField(models.TextField):

    def __init__(self, *argv, **argd):
        return super(MarkdownField, self).__init__(*argv, **argd)    

    def formfield(self, *argv, **argd):
        argd["form_class"] = MarkdownFormField
        return super(MarkdownField, self).formfield(**argd)


class MarkdownFormField(forms.CharField):

    def __init__(self, *argv, **argd):
        argd["widget"] = MonacoEditorWidget(language="markdown", endpoint="markdown")
        return super(MarkdownFormField, self).__init__(*argv, **argd)
    
    def clean(self, value):
        try:
            html = markdown.markdown(value)
        except Exception as e:
            raise ValidationError(str(e))
        return value


class SparqlField(models.TextField):

    def __init__(self, *argv, **argd):
        return super(SparqlField, self).__init__(*argv, **argd)    

    def formfield(self, *argv, **argd):
        argd["form_class"] = SparqlFormField
        return super(SparqlField, self).formfield(**argd)


class SparqlFormField(forms.CharField):

    def __init__(self, *argv, **argd):
        argd["widget"] = MonacoEditorWidget(language="sparql", endpoint="sparql")
        return super(SparqlFormField, self).__init__(*argv, **argd)
    
    def clean(self, value):
        try:
            prepareQuery(value)
        except Exception as e:
            raise ValidationError("Invalid SPARQL")
        return value


class JsonField(models.TextField):

    def __init__(self, *argv, **argd):
        return super(JsonField, self).__init__(*argv, **argd)    

    def formfield(self, *argv, **argd):
        argd["form_class"] = JsonFormField
        return super(JsonField, self).formfield(**argd)


class JsonFormField(forms.CharField):

    def __init__(self, *argv, **argd):
        argd["widget"] = MonacoEditorWidget(language="json")
        return super(JsonFormField, self).__init__(*argv, **argd)
    
    def clean(self, value):
        try:
            json.loads(value)
        except Exception as e:
            raise ValidationError("Invalid JSON")
        return value


class XmlField(models.TextField):

    def __init__(self, *argv, **argd):
        return super(XmlField, self).__init__(*argv, **argd)    

    def formfield(self, *argv, **argd):
        argd["form_class"] = XmlFormField
        return super(XmlField, self).formfield(**argd)


class XmlFormField(forms.CharField):

    def __init__(self, *argv, **argd):
        argd["widget"] = MonacoEditorWidget(language="xml")
        return super(XmlFormField, self).__init__(*argv, **argd)
    
    def clean(self, value):
        try:
            pass # check for valid XML
        except Exception as e:
            raise ValidationError("Invalid XML")
        return value
    

class WikiMarkdownField(BaseEditor):
    editor_id = "markitup"

    def get_admin_widget(self, instance=None):
        return MonacoEditorWidget(language="markdown", endpoint="markdown")

    def get_widget(self, instance=None):
        return MonacoEditorWidget(language="markdown", endpoint="markdown")

    class AdminMedia:
        css = {
        }
        js = (
        )

    class Media:
        css = {
            "all": (
            )
        }
        js = (
        )
