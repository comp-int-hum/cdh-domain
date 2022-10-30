import logging
from django.forms import Textarea, Media, Widget
from secrets import token_hex as random_token
try:
    from django.contrib.gis.db import models
except:
    from django.db import models
from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from .widgets import MonacoEditorWidget
from markdown import markdown
from wiki.editors.base import BaseEditor
from rdflib.plugins.sparql import prepareQuery
import json
from rest_framework.serializers import Field, CharField, HyperlinkedIdentityField, HyperlinkedRelatedField, RelatedField
from jsonpath import JSONPath


logger = logging.getLogger(__name__)


class AnnotationSourceField(RelatedField):
    def get_queryset(self, *argv, **argd):
        return None
    pass
    

class ViewEditField(Field):

    def __init__(self, view, edit, *argv, **argd):
        retval = super(ViewEditField, self).__init__(*argv, **argd)
        self.view = view
        self.edit = edit
        return retval

    def to_representation(self, object, *argv, **argd):
        return self.edit.to_representation(object, *argv, **argd)

    def to_internal_value(self, *argv, **argd):
        return self.edit.to_internal_value(*argv, **argd)


class UploadableTextField(CharField):
    pass


class AnnotationField(HyperlinkedIdentityField):

    def __init__(self, *argv, **argd):
        self.model_field = argd.pop("model_field", None)
        return super(AnnotationField, self).__init__(*argv, **argd)
    
    def to_representation(self, object, *argv, **argd):
        return super(AnnotationField, self).to_representation(object, *argv, *argd)

    def to_internal_value(self, *argv, **argd):
        return {}




class ActionOrInterfaceField(HyperlinkedIdentityField):
    
    def __init__(self, interface_field, *argv, **argd):
        self.nested_parent_field = argd.pop("nested_parent_field", False)
        title = argd.pop("title", None)
        retval = super(ActionOrInterfaceField, self).__init__(*argv, **argd)
        self.style["title"] = title
        self.title = title
        self.interface_field = interface_field
        self.read_only = argd.get("read_only", False)        
        return retval

    def to_representation(self, object, *argv, **argd):
        self.interface_field.style["object"] = object
        if self.nested_parent_field:
            self.interface_field.style["parent_id"] = getattr(object, self.nested_parent_field).id
        return super(ActionOrInterfaceField, self).to_representation(object, *argv, **argd)


class TabularResultsField(Field):

    def __init__(self, property_field, *argv, **argd):
        self.value_format = argd.pop("value_format", "{0}")
        self.property_field_args = argd.pop("property_field_args", {})
        for param in ["row_names_path", "column_names_path", "row_label_path", "column_label_path", "lookup_path", "rows_path"]:
            val = argd.pop(param, None)
            setattr(self, param, JSONPath(val) if val else None)
        retval = super(TabularResultsField, self).__init__(*argv, **argd)
        self.style["property_field"] = property_field        
        self.style["base_template"] = "tabular.html"
        self.style["template_pack"] = "cdh/template_pack"
        self.style["id"] = "prefix_{}".format(random_token(8))
        self.style["value_id"] = "value_{}".format(self.style["id"])
        self.style["spec_id"] = "spec_{}".format(self.style["id"])
        self.style["div_id"] = "div_{}".format(self.style["id"])
        self.style["editable"] = True
        self.field_name = "tabular_{}".format(random_token(6))
        return retval

    def get_default_value(self):
        j = getattr(self.style["object"], self.style["property_field"])(**self.property_field_args)
        retval = {}
        for param in ["row_names_path", "column_names_path", "row_label_path", "column_label_path", "lookup_path", "rows_path"]:
            val = getattr(self, param, None)
            if val:
                retval[param] = val.parse(j)[0]
        retval["rows"] = []
        for row in retval["rows_path"]: #self.rows_path.parse(j)[0]:            
            if retval.get("lookup_path", None):
                item = []
                for col_name in retval["lookup_path"]:
                    item.append(self.value_format.format(row[col_name]) if col_name in row else "")
            else:
                item = [self.value_format.format(v) for v in row]
            retval["rows"].append(item)
        return retval
    
    
class AnnotationsField(Field):
    
    def __init__(self, *argv, **argd):
        title = argd.pop("title", "Annotations")
        retval = super(AnnotationsField, self).__init__(*argv, **argd)
        self.style["title"] = title
        self.field_name = "annotations_{}".format(random_token(6))
        self.style["base_template"] = "accordion.html"
        self.style["template_pack"] = "cdh/template_pack"
        return retval

    def get_default_value(self):
        return self.style["object"].annotations()
    
    def to_representation(self, object, *argv, **argd):
        return object.annotations()

    def to_internal_value(self, *argv, **argd):
        return {}


class VegaField(Field):
    visual_only = True
    def __init__(self, vega_class, *argv, **argd):
        property_field = argd.pop("property_field", None)
        self.property_field_args = argd.pop("property_field_args", {})
        self.title = argd.pop("title", "")
        retval = super(VegaField, self).__init__(*argv, **argd)
        self.vega_class = vega_class
        self.style["property_field"] = property_field
        self.style["base_template"] = "vega.html"
        self.style["template_pack"] = "cdh/template_pack"
        self.style["id"] = "{}".format(random_token(8))
        self.style["value_id"] = "value_{}".format(self.style["id"])
        self.style["spec_id"] = "spec_{}".format(self.style["id"])
        self.style["div_id"] = "div_{}".format(self.style["id"])
        self.style["editable"] = True
        self.field_name = "vega_{}".format(random_token(6))
        return retval

    def get_attribute(self, object, **argd):
        return getattr(object, self.style["property_field"])(**self.property_field_args)

    def get_default_value(self):
        return self.vega_class(
            getattr(self.style["object"], self.style["property_field"])(**self.property_field_args),
            self.style["div_id"]
        ).json
    
    def to_representation(self, object, *argv, **argd):
        return self.vega_class(
            object,
            #getattr(object, self.style["property_field"])(**self.property_field_args),
            self.style["div_id"]
            #object
        ).json

    
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
        self.style["editable"] = False
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
    

class MarkdownEditorField(MonacoEditorField):

    def __init__(self, *argv, **argd):
        retval = super(MarkdownEditorField, self).__init__(*argv, **argd)
        self.style["rendering_url"] = "markdown"
        self.style["hide_label"] = True
        

class JsonEditorField(MonacoEditorField):
    def __init__(self, *argv, **argd):
        argd["language"] = "json"
        retval = super(JsonEditorField, self).__init__(*argv, **argd)
        #self.style["rendering_url"] = "markdown"
        self.style["hide_label"] = True

        
class SparqlEditorField(MonacoEditorField):
    def __init__(self, *argv, **argd):
        argd["language"] = "sparql"
        retval = super(SparqlEditorField, self).__init__(*argv, **argd)
        self.style["rendering_url"] = "sparql"
        self.style["hide_label"] = True
        
    
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
