import logging
from django.forms import Textarea, Media, Widget
from secrets import token_hex as random_token
from django.contrib.gis.db import models
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from .widgets import MonacoEditorWidget
import markdown
from wiki.editors.base import BaseEditor
from rdflib.plugins.sparql import prepareQuery
import json
from rest_framework.serializers import Field, CharField, HyperlinkedIdentityField
from jsonpath import JSONPath


logger = logging.getLogger(__name__)


class ActionOrInterfaceField(HyperlinkedIdentityField):
    
    def __init__(self, interface_field, *argv, **argd):
        self.nested_parent_field = argd.pop("nested_parent_field", False)
        retval = super(ActionOrInterfaceField, self).__init__(*argv, **argd)
        self.interface_field = interface_field
        self.read_only = argd.get("read_only", False)

        #self.interface_field.style["property_name"] = property_name
        return retval

    def to_representation(self, object, *argv, **argd):
        self.interface_field.style["object"] = object        
        if self.nested_parent_field:
            self.interface_field.style["parent_id"] = getattr(object, self.nested_parent_field).id
        return super(ActionOrInterfaceField, self).to_representation(object, *argv, **argd)


class TabularResultsField(Field):

    def __init__(self, property_field, *argv, **argd):
        retval = super(TabularResultsField, self).__init__(*argv, **argd)
        self.style["property_field"] = property_field        
        self.style["base_template"] = "tabular.html"
        self.style["template_pack"] = "cdh/template_pack"
        self.style["id"] = "prefix_{}".format(random_token(8))
        self.style["value_id"] = "value_{}".format(self.style["id"])
        self.style["spec_id"] = "spec_{}".format(self.style["id"])
        self.style["div_id"] = "div_{}".format(self.style["id"])
        self.style["editable"] = True
        self.field_name = "vega_{}".format(random_token(6))
        self.column_names_path = JSONPath(argd.get("column_names_path", "head.vars"))
        self.rows_path = JSONPath(argd.get("rows_path", "results.bindings"))
        self.value_format = argd.get("value_format", "{0[value]}")
        return retval

    def get_default_value(self):
        j = getattr(self.style["object"], self.style["property_field"])()
        col_names = self.column_names_path.parse(j)[0]
        retval = {
            "column_names" : col_names,
            "rows" : []
        }
        for row in self.rows_path.parse(j)[0]:
            item = []
            for col_name in col_names:
                item.append(self.value_format.format(row[col_name]) if col_name in row else "")
            retval["rows"].append(item)        
        return retval
    
    
class VegaField(Field):

    def __init__(self, vega_class, *argv, **argd):
        property_field = argd.pop("property_field", None)
        retval = super(VegaField, self).__init__(*argv, **argd)
        self.vega_class = vega_class
        self.style["property_field"] = property_field
        self.style["base_template"] = "vega.html"
        self.style["template_pack"] = "cdh/template_pack"
        self.style["id"] = "prefix_{}".format(random_token(8))
        self.style["value_id"] = "value_{}".format(self.style["id"])
        self.style["spec_id"] = "spec_{}".format(self.style["id"])
        self.style["div_id"] = "div_{}".format(self.style["id"])
        self.style["editable"] = True
        self.field_name = "vega_{}".format(random_token(6))
        return retval

    def get_default_value(self):
        return self.vega_class(getattr(self.style["object"], self.style["property_field"])()).json
    
    def to_representation(self, object, *argv, **argd):
        return self.vega_class(object).json


class MonacoEditorField(CharField):
    def __init__(self, *argv, **argd):
        property_field = argd.pop("property_field", None)        
        detail_endpoint = argd.pop("detail_endpoint", False)
        endpoint = argd.pop("endpoint", False)
        language = argd.pop("language", "")
        self.nested_parent_field = argd.pop("nested_parent_field", None)
        retval = super(MonacoEditorField, self).__init__(*argv, **argd)
        self.style["property_field"] = property_field
        self.style["base_template"] = "editor.html"
        self.style["css"] = self.media._css["all"]
        self.style["js"] = self.media._js
        self.style["id"] = "prefix_{}".format(random_token(8))
        self.style["value_id"] = "value_{}".format(self.style["id"])
        self.style["output_id"] = "output_{}".format(self.style["id"])
        self.style["language"] = language
        self.style["detail_endpoint"] = detail_endpoint
        self.style["endpoint"] = endpoint
        self.style["template_pack"] = "cdh/template_pack"
        self.style["editable"] = True
        self.field_name = "monaco_{}".format(random_token(6))
        return retval

    def get_default_value(self):
        return ""

    @property
    def media(self):
        return Media(
            css = {
                'all': (
                    "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.0-dev.20220627/min/vs/editor/editor.main.min.css",
                ),
            },
            js = (
                "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.34.0-dev.20220625/min/vs/loader.min.js",
            )
        )
    

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
        
