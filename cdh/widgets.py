from django.forms import Textarea, Media, Widget
from django.template.loader import get_template
from sekizai.context import SekizaiContext
from secrets import token_hex as random_token

class VegaWidget(Widget):
    template_name = "cdh/vega.html"
    def __init__(self, vega_class, *argv, **argd):
        super(VegaWidget, self).__init__(*argv, **argd)
        self.vega_class = vega_class
        
    def get_context(self, name, value, attrs):
        ctx = super(VegaWidget, self).get_context(name, value, attrs)
        ctx["vega_spec"] = self.vega_class(value).json
        ctx["spec_identifier"] = "s_{}".format(random_token(8))
        ctx["div_identifier"] = "d_{}".format(random_token(8))
        return ctx
        
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


class MonacoEditorWidget(Textarea):
    
    template_name = "cdh/editor.html"
    def __init__(self, *args, **kwargs):
        self.language = kwargs.get("language", "javascript")
        self.default_value = kwargs.get("default_value", "")
        default_attrs = {"language" : kwargs.get("language", "javascript"), "field_name" : kwargs.get("name", "content")}
        default_attrs.update(kwargs.get("attrs", {}))        
        super().__init__(default_attrs)


    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["css"] = self.media._css["all"]
        context["js"] = self.media._js
        context["widget"]["value_id"] = "value_{}".format(context["widget"]["attrs"]["id"])
        context["widget"]["value"] = context["widget"]["value"] if context["widget"].get("value", None) else self.default_value
        context["widget"]["list_value"] = context["widget"]["value"].split("\n")        
        return context

    def value_from_datadict(self, data, files, name):
        return super().value_from_datadict(data, files, name)
    
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

