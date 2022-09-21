import re
import logging
from collections import OrderedDict
from django import template
from django.template import loader
from django.urls import NoReverseMatch, reverse
from django.utils.encoding import iri_to_uri
from django.utils.html import escape, format_html, smart_urlquote
from django.utils.safestring import mark_safe
from rest_framework.compat import apply_markdown, pygments_highlight
from rest_framework.renderers import HTMLFormRenderer
from rest_framework.utils.urls import replace_query_param
from ..renderers import CdhHTMLFormRenderer


logger = logging.getLogger(__name__)
register = template.Library()


@register.simple_tag
def cdh_render_form(serializer, template_pack=None):
    try:
        style = {'template_pack': template_pack} if template_pack else {}
        renderer = CdhHTMLFormRenderer()
        style["object_id"] = serializer.data.get("id", None)
        return renderer.render(serializer.data, None, {'style': style})
    except Exception as e:
        logger.info("Exception: %s", e)
        return ""
