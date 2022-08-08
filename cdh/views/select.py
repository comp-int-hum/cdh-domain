from django.template.engine import Engine
from django.template import Context
from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views import View
from django.utils.safestring import mark_safe
template_engine = Engine.get_default()
from .mixins import NestedMixin

class SelectView(NestedMixin, SingleObjectMixin, View):
    template_name = "cdh/simple_interface.html"
    model = None
    related_model = None
    relationship = None
    child_name_field = None
    related_url = None
    preamble = None
    limit = 100

    def get_object(self):
        try:
            return SingleObjectMixin.get_object(self)
        except:
            return None
    
    def get_context_data(self, request, *argv, **argd):
        self.object = self.get_object()
        self.request = request
        self.from_htmx = request.headers.get("Hx-Request", False) and True
        ctx = super(SelectView, self).get_context_data(*argv, **argd)
        ctx["content"] = self.render(request)
        ctx["preamble"] = self.preamble
        return ctx
    
    def render(self, request):
        obj = self.get_object()
        related_objects = self.related_model.objects.filter(**{self.relationship : obj}).select_related()[0:self.limit]
        content = template_engine.get_template("cdh/snippets/select.html").render(
            Context(
                {
                    "options" : related_objects,
                    #"uid" : self.uid,
                    #"sid" : self.sid,
                    "related_url" : self.related_url,
                }
            )
        )
        return mark_safe(content)

    def get(self, request, *argv, **argd):
        return render(request, self.template_name, {"content" : self.render(request), "preamble" : self.preamble})
