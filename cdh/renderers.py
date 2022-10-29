import logging
from django.template import loader
from rest_framework.renderers import TemplateHTMLRenderer, HTMLFormRenderer
from rest_framework.utils.serializer_helpers import BoundField
from cdh.fields import ActionOrInterfaceField
from sekizai.context import SekizaiContext

logger = logging.getLogger(__name__)


class CdhHTMLFormRenderer(HTMLFormRenderer):
    
    def __init__(self, *argv, **argd):
        retval = super(CdhHTMLFormRenderer, self).__init__(*argv, **argd)
        return retval

    def render(self, data, accepted_media_type=None, renderer_context=None):
        for style_field_name in ["mode", "tab_view", "uid", "index"]:
            if style_field_name in renderer_context:
                renderer_context["style"][style_field_name] = renderer_context[style_field_name]
        self.uid = renderer_context["uid"]
        self.request = renderer_context.get("request", None)
        return super(CdhHTMLFormRenderer, self).render(data, accepted_media_type=accepted_media_type, renderer_context=renderer_context)
    
    def render_field(self, field, parent_style, *argv, **argd):
        field.context["request"] = self.request
        if isinstance(field._field, ActionOrInterfaceField):
            # if GET then pull value from object, else empty
            inter = field._field.interface_field
            inter.context["request"] = self.request
            if hasattr(inter, "get_actual_field"):
                inter = inter.get_actual_field(parent_style)
            #field = BoundField(field._field.interface_field, field._field.interface_field.get_default_value(), [])
            field = BoundField(inter, inter.get_default_value(), [])
            #print(field)
            # style = self.default_style[field].copy()
            # style.update(field.style)
            # if 'template_pack' not in style:
            #     style['template_pack'] = parent_style.get('template_pack', self.template_pack)
            # style['renderer'] = self

            # # Get a clone of the field with text-only value representation.
            # field = field.as_form_field()

            # if style.get('input_type') == 'datetime-local' and isinstance(field.value, str):
            #     field.value = field.value.rstrip('Z')

            # if 'template' in style:
            #     template_name = style['template']
            # else:
            #     template_name = style['template_pack'].strip('/') + '/' + style['base_template']

            # template = loader.get_template(template_name)
            # context = {'field': field, 'style': style, "request" : self.request}
            # return template.render(context)

        retval = super(CdhHTMLFormRenderer, self).render_field(field, parent_style, *argv, **argd)
        return retval
    

class CdhTemplateHTMLRenderer(TemplateHTMLRenderer):
    format = "cdh"
    
    def get_template_context(self, data, renderer_context):
        context = super(CdhTemplateHTMLRenderer, self).get_template_context(data, renderer_context)
        context = {"items" : context} if isinstance(context, list) else context
        for k, v in renderer_context.items():
            if not context.get(k):
                context[k] = v
            #else:
            #    logger.info("Not replacing %s with %s for context item %s", context.get(k), v, k)
            #print(list(context.keys()))
            
        return context
