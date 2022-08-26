import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import re_path, reverse
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views import View
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_users_with_perms, get_groups_with_perms, remove_perm
from django.utils.safestring import mark_safe
from django.template.engine import Engine
from django.template import Context
from .mixins import NestedMixin, ButtonsMixin
from .base import BaseView


template_engine = Engine.get_default()


class TabsView(BaseView): #PermissionsMixin, NestedMixin, SingleObjectMixin, View):
    """
    A TabView renders its "tabs" as siblings in a Bootstrap tab component.
    The as_view() method accepts the following arguments:

      tabs
      preamble=None
      model=None
      can_delete=False

    Where "tabs" is a list whose entries are dictionaries with fields:

      url
      title=None

    Only one tab may be active at a given time, and the state should be
    preserved across page refresh/other navigation.
    """
    tabs = None
    model = None
    template = "cdh/simple_interface.html"
    can_delete = False
    can_update = False
    can_create = False
    object = None
    buttons = None
    preamble = None
    
    def __init__(self, *argv, **argd):        
        super(TabsView, self).__init__(*argv, **argd)        

    def get_object(self):
        try:
            return SingleObjectMixin.get_object(self)
        except:
            return None
        
    def get_context_data(self, request, *argv, **argd):
        self.object = self.get_object()
        self.request = request
        self.from_htmx = request.headers.get("Hx-Request", False) and True
        
        ctx = super(TabsView, self).get_context_data(*argv, **argd)
        
        ctx["tabs"] = self.tabs
        ctx["instance"] = self.object
        return ctx
    
    def render(self, ctx):
        content = template_engine.get_template("cdh/snippets/tabs.html").render(
            Context(ctx)
        )
        return mark_safe(content)
    
    def get(self, request, *argv, **argd):
        obj = self.get_object()
        self.obj_perms = [x.split("_")[0] for x in (get_perms(request.user, obj) if obj else [])]
        ctx = self.get_context_data(request)
        ctx["path"] = request.path_info
        ctx["object"] = obj
        ctx["content"] = self.render(ctx)
        state = getattr(obj, "state", None)
        if state == "PR":
            return render(request, "cdh/async_processing.html", ctx)
        elif state == "ER":
            return render(request, "cdh/async_error.html", ctx)
        return render(request, self.template, ctx)

    def delete(self, request, *argv, **argd):
        from_htmx = request.headers.get("Hx-Request", False) and True
        obj = self.get_object()
        obj_id = obj.id
        obj.delete()
        resp = HttpResponseRedirect(reverse("{}:{}_list".format(obj._meta.app_label, obj._meta.model_name)))
        resp.headers["HX-Trigger"] = """{{"cdhEvent" : {{"type" : "delete", "app" : "{app}", "model" : "{model}", "id" : "{id}"}}}}""".format(
            app=self.model._meta.app_label,
            model=self.model._meta.model_name,
            id=obj_id
        )
        return resp
