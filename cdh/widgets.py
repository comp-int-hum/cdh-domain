from django.forms import Textarea, Media, Widget
from django.template.loader import get_template
from sekizai.context import SekizaiContext
from secrets import token_hex as random_token


class TableWidget(Widget):
    def __init__(self, *argv, **argd):
        super(TableWidget, self).__init__(*argv, **argd)

    def get_context(self, name, value, attrs):
        context = super(TableWidget, self).get_context(name, value, attrs)
        return context


class VegaWidget(Widget):
    template_name = "cdh/vega.html"
    preamble = None

    def __init__(self, vega_class, *argv, preamble=None, **argd):
        super(VegaWidget, self).__init__(*argv, **argd)
        self.vega_class = vega_class
        self.preamble = preamble
        
    def get_context(self, name, value, attrs):
        context = super(VegaWidget, self).get_context(name, value, attrs)

        context["widget"]["attrs"]["id"] = "prefix_{}".format(random_token(8))
        self.prefix = context["widget"]["attrs"]["id"]
        context["widget"]["spec_id"] = "spec_{}".format(context["widget"]["attrs"]["id"])
        context["widget"]["div_id"] = "div_{}".format(context["widget"]["attrs"]["id"])
        context["widget"]["element_id"] = "element_{}".format(context["widget"]["attrs"]["id"])

        context["vega_spec"] = self.vega_class(value, prefix=self.prefix).json
        context["spec_identifier"] = "spec_{}".format(context["widget"]["attrs"]["id"]) #"s_{}".format(self.prefix)
        context["div_identifier"] = "div_{}".format(context["widget"]["attrs"]["id"]) #"d_{}".format(self.prefix)
        context["element_identifier"] = "element_{}".format(context["widget"]["attrs"]["id"]) #"d_{}".format(self.prefix)
        return context


class MonacoEditorWidget(Textarea):
    template_name = "cdh/template_pack/editor.html"
    id = None #"prefix".format(random_token(8))
    #value_id = None #"value_prefix_{}".format(id)
    
    def __init__(self, *args, **kwargs):
        self.language = kwargs.get("language", "javascript")
        self.default_value = kwargs.get("default_value", "")
        #self.id = "prefix_{}".format(random_token(8))
        #self.value_id = "value_{}".format(self.id)
        #self.output_id = "output_{}".format(self.id)
        self.field_name = kwargs.get("name", "content")
        #print(self.field_name)
        default_attrs = {
            "language" : kwargs.get("language", "javascript"),
            "field_name" : kwargs.get("name", "content"),
            "endpoint" : kwargs.get("endpoint", None),

        }
        default_attrs.update(kwargs.get("attrs", {}))
        super(MonacoEditorWidget, self).__init__(default_attrs)

    def get_context(self, name, value, attrs):
        context = super(MonacoEditorWidget, self).get_context(name, value, attrs)

        context["css"] = self.media._css["all"]
        context["js"] = self.media._js
        context["widget"]["attrs"]["id"] = "prefix_{}".format(random_token(8))
        context["widget"]["value_id"] = "value_{}".format(context["widget"]["attrs"]["id"])
        context["widget"]["output_id"] = "output_{}".format(context["widget"]["attrs"]["id"])
        context["widget"]["value"] = context["widget"]["value"] if context["widget"].get("value", None) else self.default_value
        rid = "prefix_{}".format(random_token(8))
        context["field"] = {
            "name" : self.field_name,
            "value" : value
        }
        context["style"] = {
            #"property_field" : property_field,
            
            "base_template" : "editor.html",
            "css" : self.media._css["all"],
            "js" : self.media._js,
            "id" : rid,
            "value_id" : "value_{}".format(rid),
            "output_id" : "output_{}".format(rid),
            "language" : self.language,
            #"detail_endpoint" : self.language,
            "endpoint" : self.language,
            "template_pack" : "cdh/template_pack",
            "editable" : True,
            "field_name" : "monaco_{}".format(random_token(6)),
        }

        return context

    def value_from_datadict(self, data, files, name):
        return super(MonacoEditorWidget, self).value_from_datadict(data, files, name)
    
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
