from django.forms import Textarea, Media, Widget
from django.template.loader import get_template
from cdh.widgets import MonacoEditorWidget


class MachineLearningModelInteractionWidget(Textarea):
    
    template_name = "cdh/editor.html"
    def __init__(self, *args, **kwargs):
        self.language = kwargs.get("language", "")
        self.default_value = kwargs.get("default_value", "")
        default_attrs = {"language" : kwargs.get("language", ""), "field_name" : kwargs.get("name", "interaction"), "class" : "cdh-model-interaction"}
        default_attrs.update(kwargs.get("attrs", {}))        
        super().__init__(default_attrs)


    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["css"] = self.media._css["all"]
        context["js"] = self.media._js
        context["widget"]["value_id"] = "value_{}".format(context["widget"]["attrs"]["id"])
        context["widget"]["output_id"] = "output_{}".format(context["widget"]["attrs"]["id"])
        context["widget"]["value"] = context["widget"]["value"] if context["widget"].get("value", None) else self.default_value
        context["widget"]["list_value"] = context["widget"]["value"].split("\n")
        context["widget"]["class"] = "cdh-model-interaction"
        print(context)
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

