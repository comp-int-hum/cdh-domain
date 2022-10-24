import re
import logging
from collections import OrderedDict
from django import template
from django.template import loader
from django.urls import NoReverseMatch, reverse
from django.utils.encoding import iri_to_uri
from django.utils.html import escape, format_html, smart_urlquote
from django.utils.safestring import mark_safe
from django.contrib.contenttypes.models import ContentType
from guardian.shortcuts import get_perms
from rest_framework.compat import apply_markdown, pygments_highlight
from rest_framework.renderers import HTMLFormRenderer
from rest_framework.utils.urls import replace_query_param
from ..renderers import CdhHTMLFormRenderer
from ..models import Documentation
from ..serializers import DocumentationSerializer


logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag(takes_context=True)
def cdh_render_form(context, serializer, template_pack=None, mode="view"):
    try:
        style = {'template_pack': template_pack} if template_pack else {}
        #args = {}
        #for name in ["uid"]:
        #    if name in context:
        #        args[name] = context[name]
        renderer = CdhHTMLFormRenderer()
        try:
            style["object_id"] = serializer.data.get("id", None)
        except:
            style["object_id"] = None
        tab_view = mode == "view" and hasattr(serializer, "Meta") and getattr(serializer.Meta, "tab_view", False)
        keep = getattr(serializer.Meta, "{}_fields".format(mode), None) if hasattr(serializer, "Meta") else None
        if keep:
            serializer.fields = {field_name : field for field_name, field in serializer.fields.items() if field_name in keep}
        #uid = context["view"].uid
        for i, field in enumerate(serializer.fields):
            serializer.fields[field].style["index"] = i
            if mode in ["edit", "create"]:
                serializer.fields[field].style["editable"] = True
                #print(context)
        return renderer.render(serializer.data, None, {'style': style, "mode" : mode, "tab_view" : tab_view, "request" : context.get("request")})
    except Exception as e:
        logger.info("Exception: %s", e)
        raise e
        return ""


@register.simple_tag(takes_context=True)
def cdh_get_documentation_object(context, view_name, item):
    #print(item, type(item), view_name)
    #if "request" not in context:
    #    return None
    if isinstance(item, (str, dict)):
        content_type = None
        object_id = None
    elif item.is_model() and not item.is_object():
        content_type = ContentType.objects.get_for_model(item)
        object_id = None
    elif item.is_object():
        content_type = ContentType.objects.get_for_model(item._meta.model)
        object_id = item.id
    else:
        logger.error("Something strange: %s", item)
        content_type = None
        object_id = None
    content_type_id = content_type.id if content_type else None
    docs = Documentation.objects.filter(
        view_name=view_name,
        content_type=content_type,
        object_id=object_id
    )
    ret_obj = docs[0] if len(docs) > 0 else None
    if ret_obj:
        ret_ser = DocumentationSerializer(ret_obj, context=context)
        can_edit = Documentation.get_add_perm() in get_perms(context["request"].user, ret_obj)
    else:
        data = {
            "view_name": view_name,
            "content_type" : content_type_id,
            "object_id" : object_id,
            "name" : "_".join([str(x) for x in [view_name, content_type_id, object_id] if x]),
        }
        ret_ser = DocumentationSerializer(data=data, context=context)
        can_edit = False if "request" not in context else Documentation.get_add_perm() in get_perms(context["request"].user, Documentation)
        ret_ser.is_valid()
    retval = {
        "object" : ret_obj if ret_obj else Documentation(
            name="_".join([str(x) for x in [view_name, content_type_id, object_id] if x]),
            view_name=view_name,
            content_type=content_type,
            object_id=object_id
        ),
        "can_edit" : can_edit,
        "serializer" : ret_ser
    }
    #print(123)    
    return retval

