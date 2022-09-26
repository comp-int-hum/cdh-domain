import logging
from django.template import loader
from rest_framework.renderers import TemplateHTMLRenderer, HTMLFormRenderer
from rest_framework.utils.serializer_helpers import BoundField
from cdh.fields import ActionOrInterfaceField


logger = logging.getLogger(__name__)


class CdhHTMLFormRenderer(HTMLFormRenderer):
    
    def __init__(self, *argv, **argd):
        retval = super(CdhHTMLFormRenderer, self).__init__(*argv, **argd)
        return retval

    def render(self, data, accepted_media_type=None, renderer_context=None):
        for style_field_name in ["mode", "tab_view", "uid", "index"]:
            renderer_context["style"][style_field_name] = renderer_context.get(style_field_name)
        return super(CdhHTMLFormRenderer, self).render(data, accepted_media_type=accepted_media_type, renderer_context=renderer_context)
    
    def render_field(self, field, parent_style, *argv, **argd):        
        if isinstance(field._field, ActionOrInterfaceField):
            # if GET then pull value from object, else empty
            
            field = BoundField(field._field.interface_field, field._field.interface_field.get_default_value(), [])
            #field = BoundField(field._field.interface_field) #, N, [])
            style = self.default_style[field].copy()
            style.update(field.style)
            if 'template_pack' not in style:
                style['template_pack'] = parent_style.get('template_pack', self.template_pack)
            style['renderer'] = self

            # Get a clone of the field with text-only value representation.
            field = field.as_form_field()

            if style.get('input_type') == 'datetime-local' and isinstance(field.value, str):
                field.value = field.value.rstrip('Z')

            if 'template' in style:
                template_name = style['template']
            else:
                template_name = style['template_pack'].strip('/') + '/' + style['base_template']

            template = loader.get_template(template_name)
            context = {'field': field, 'style': style}
            return template.render(context)
        #print(field.name, field.style)
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
        print(context.get("uid"))
        return context
