
import logging
# from cdh import settings
# from cdh.models import User
# from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
# from django.urls import re_path, reverse
# from django.views.generic.list import ListView, MultipleObjectMixin
# from django.utils.decorators import classonlymethod

# from django.views.generic.base import TemplateView, TemplateResponseMixin, ContextMixin
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
# from django.views.generic import DetailView
# from django.views.generic.edit import CreateView, DeleteView, UpdateView, DeletionMixin, ModelFormMixin, ProcessFormView
from django.views import View
# from django.contrib.auth.models import Group
# from django.core.cache import cache
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_users_with_perms, get_groups_with_perms, remove_perm
# from guardian.forms import UserObjectPermissionsForm, GroupObjectPermissionsForm

from django.utils.safestring import mark_safe
# from django.utils.text import slugify
# from django.contrib.auth.decorators import login_required, permission_required
# from . import models, forms
# from .widgets import VegaWidget

# if settings.USE_LDAP:
#     from django_auth_ldap.backend import LDAPBackend
from django.template.engine import Engine
from django.template import Context

template_engine = Engine.get_default()


from .mixins import NestedMixin

class TabsView(NestedMixin, SingleObjectMixin, View):
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
        
    def get_context_data(self, request, obj_perms, *argv, **argd):
        self.object = self.get_object()
        self.request = request
        self.from_htmx = request.headers.get("Hx-Request", False) and True
        
        retval = super(TabsView, self).get_context_data(*argv, **argd)
        retval["tabs"] = self.tabs
        retval["instance"] = self.object
        if self.buttons:
            retval["buttons"] = self.buttons
        else:
            retval["buttons"] = []
            obj = self.get_object()
            if self.can_update and "change" in obj_perms:
                retval["buttons"].append(
                    {
                        "label" : "Save",
                        "style" : "primary",
                        "hx_swap" : "none",
                        "hx_post" : request.path_info,
                    }                    
                )
            if self.can_delete and "delete" in obj_perms:
                retval["buttons"].append(
                    {
                        "label" : "Delete",
                        "style" : "danger",
                        "hx_confirm" : "Are you sure you want to delete this object and any others derived from it?",
                        "hx_swap" : "none",
                        "hx_delete" : request.path_info,
                    }
                )
        return retval
    
    def render(self, ctx): #request):
        content = template_engine.get_template("cdh/snippets/tabs.html").render(
            Context(ctx)
        )
        return mark_safe(content)
    
    def get(self, request, *argv, **argd):        
        obj = self.get_object()
        obj_perms = [x.split("_")[0] for x in (get_perms(request.user, obj) if obj else [])]
        ctx = self.get_context_data(request, obj_perms)
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
        #print("Deleted an instance of {} and redirecting to {}".format(self.model, resp))        
        return resp
