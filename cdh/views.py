from django.forms import ModelForm, modelform_factory, FileField
import re
import logging
from secrets import token_hex as random_token

from cdh import settings
from cdh.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import re_path, reverse
from django.views.generic.list import ListView, MultipleObjectMixin
from django.utils.decorators import classonlymethod

from django.views.generic.base import TemplateView, TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView, DeletionMixin, ModelFormMixin, ProcessFormView
from django.views import View
from django.contrib.auth.models import Group
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm

from schedule.feeds import CalendarICalendar, UpcomingEventsFeed
from schedule.models import Calendar
from schedule.periods import Day, Month, Week, Year
from schedule.views import (
    CalendarByPeriodsView,
    CalendarView,
    CancelOccurrenceView,
    CreateEventView,
    CreateOccurrenceView,
    DeleteEventView,
    EditEventView,
    EditOccurrenceView,
    EventView,
    FullCalendarView,
    OccurrencePreview,
    OccurrenceView,
    api_move_or_resize_by_code,
    api_occurrences,
    api_select_create,
)
from django.utils.safestring import mark_safe
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required, permission_required
from . import models, forms
from .widgets import VegaWidget

if settings.USE_LDAP:
    from django_auth_ldap.backend import LDAPBackend


class CdhView(DeletionMixin, UpdateView):
    """
    CdhView is intended as the "ground-level" view for a single CDH-related object
    in a CRUD form.  The as_view() method accepts the following arguments:

      preamble
      model
      form_class
      fields
      extra_fields
      initial
      can_create
      can_delete
      can_update
      create_lambda: returns tuple of (object, response)
      delete_lambda
      update_lambda

    Depending on the (successful) action, its responses will set the following headers:

      "deleted{app}{model}":
      "created{app}{model}":
      "updated{app}{model}{id}":

    Furthermore, if the created object is asynchronous and in a "processing" state, the
    returned content will be a self-updating HTMX placeholder.  If in an "error" state,
    a non-updating placeholder will be returned.  In both cases, any message on the
    object will be displayed as well.

    Created objects will default to allowing public view, with all additional permissions
    assigned to the creator.
    """
    template_name = "cdh/simple_interface.html"
    extra_fields = {}
    form_class = None
    post_lambda = None
    create_lambda = None
    delete_lambda = None
    update_lambda = None
    form_htmx = {
    }
    form_id = "form_{}".format(random_token(6))
    buttons = None
    can_delete = False
    can_update = False
    can_create = False
    object = None
    fields = []
    preamble = None
    
    def __init__(self, *argv, **argd):        
        super(CdhView, self).__init__(*argv, **argd)
            
    def get_object(self):
        try:
            return super(CdhView, self).get_object()
        except:
            return None
        
    def get_context_data(self, request, from_htmx, model_perms, obj_perms, *argv, **argd):
        retval = super(CdhView, self).get_context_data(*argv, **argd)
        if self.buttons:
            retval["buttons"] = self.buttons
        elif self.can_create and request.user.username != "AnonymousUser":
            retval["buttons"] = [
                {
                    "label" : "Create",
                    "style" : "primary",
                    "hx_swap" : "none",
                    "hx_post" : request.path_info,
                }
            ]
        else:
            retval["buttons"] = []
            if self.can_update and "change" in obj_perms:
                retval["buttons"].append(
                    {
                        "label" : "Save",
                        "style" : "primary",
                        "hx_target" : "#{}".format(self.form_id),
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
                        "hx_target" : "#{}".format(self.form_id),
                        "hx_swap" : "none",
                        "hx_delete" : request.path_info,
                    }
                )
        retval["form_id"] = self.form_id
        retval["from_htmx"] = from_htmx
        if self.preamble:
            retval["preamble"] = self.preamble
        return retval
        
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        resp = super(CdhView, self).form_valid(form)
        return resp

    def form_invalid(self, form):
        resp = super(CdhView, self).form_invalid(form)
        return resp
    
    def get_form_class(self):
        if self.form_class:
            return self.form_class
        else:
            class AugmentedForm(ModelForm):
                def __init__(sself, *argv, **argd):
                    super(AugmentedForm, sself).__init__(*argv, **argd)
                    for k, v in self.extra_fields.items():
                        if isinstance(v, tuple):
                            sself.fields[k] = v[0](**v[1])
                        else:
                            sself.fields[k] = v()
                class Meta:
                    model = self.model
                    fields = self.fields
            return AugmentedForm
    
    def get(self, request, *argv, **argd):
        from_htmx = request.headers.get("Hx-Request", False) and True
        self.request = request
        self.initial["created_by"] = request.user
        print(
            "GET to {} with HX-Trigger={} and HX-Request={}".format(
                request.path_info,
                request.headers.get("HX-Trigger"),
                request.headers.get("HX-Request")
            )
        )
        obj = self.get_object()
        state = getattr(obj, "state", None)
        model_perms = [x.split("_")[0] for x in get_perms(request.user, self.model)]
        obj_perms = [x.split("_")[0] for x in (get_perms(request.user, obj) if obj else [])]
        ctx = self.get_context_data(request, from_htmx, model_perms, obj_perms)
        if obj:
            ctx["form"] = self.get_form_class()(instance=obj)
        else:
            ctx["form"] = self.get_form_class()(initial=self.initial)
        ctx["htmx_request"] = from_htmx
        ctx["path"] = request.path_info
        ctx["object"] = obj
        if state == "PR":
            return render(request, "cdh/async_processing.html", ctx)
        elif state == "ER":
            return render(request, "cdh/async_error.html", ctx)
        else:
            return self.render_to_response(ctx)

    def post(self, request, *argv, **argd):
        from_htmx = request.headers.get("Hx-Request", False) and True
        self.request = request
        obj = self.get_object()
        print(
            "POST to {} with HX-Trigger={} and HX-Request={}".format(
                request.path_info,
                request.headers.get("HX-Trigger"),
                request.headers.get("HX-Request")
            )
        )
        if obj:
            if self.update_lambda:
                resp = self.update_lambda(request, *argv, **argd)
            else:
                form = self.get_form_class()(request.POST, instance=obj)
                if form.has_changed():
                    form.save()
                resp = HttpResponse() #Redirect(obj.get_absolute_url())
            #if from_htmx:
            resp.headers["HX-Trigger"] = """{{"cdhEvent" : {{"type" : "update", "app" : "{app}", "model" : "{model}", "id" : "{id}"}}}}""".format(
                app=self.model._meta.app_label,
                model=self.model._meta.model_name,
                id=obj.id
            )
            print("Updated {} instance {} and redirecting to {}".format(self.model, obj, resp))
            print(resp.headers)            
            return resp
        else:
            if self.create_lambda:
                obj, resp = self.create_lambda(self, request, *argv, **argd)
            else:
                obj = self.get_form_class()(request.POST).save()                
                resp = HttpResponse() #HttpResponseRedirect(obj.get_absolute_url())
            assign_perm("{}.view_{}".format(self.model._meta.app_label, self.model._meta.model_name), request.user, obj)
            assign_perm("{}.delete_{}".format(self.model._meta.app_label, self.model._meta.model_name), request.user, obj)
            assign_perm("{}.change_{}".format(self.model._meta.app_label, self.model._meta.model_name), request.user, obj)
            #assign_perm("{}.view_{}".format(self.model._meta.app_label, self.model._meta.model_name), User.get_anonymous(), obj)
            obj.created_by = request.user
            obj.save()
            resp.headers["HX-Trigger"] = """{{"cdhEvent" : {{"type" : "create", "app" : "{app}", "model" : "{model}", "id" : "{id}"}}}}""".format(
                app=self.model._meta.app_label,
                model=self.model._meta.model_name,
                id=obj.id
            )
            print("Created an instance of {}".format(self.model))
            print(resp.headers)
            return resp

    def delete(self, request, *argv, **argd):
        from_htmx = request.headers.get("Hx-Request", False) and True
        self.request = request
        print(
            "DELETE to {} with HX-Trigger={} and HX-Request={}".format(
                request.path_info,
                request.headers.get("HX-Trigger"),
                request.headers.get("HX-Request")
            )
        )
        obj = self.get_object()
        obj_id = obj.id
        if self.delete_lambda:
            resp = self.delete_lambda(request, *argv, **argd)
        else:
            
            obj.delete()
            resp = HttpResponse()
            #resp = HttpResponseRedirect(reverse("{}:{}_list".format(obj._meta.app_label, obj._meta.model_name)))
        #if from_htmx:
        
        resp.headers["HX-Trigger"] = """{{"cdhEvent" : {{"type" : "delete", "app" : "{app}", "model" : "{model}", "id" : "{id}"}}}}""".format(
            app=self.model._meta.app_label,
            model=self.model._meta.model_name,
            id=obj_id
        )
        print("Deleted an instance of {} and redirecting to {}".format(self.model, resp))
        print(resp.headers)        
        return resp


class VegaView(SingleObjectMixin, View):
    """
    A VegaView renders a dynamic Vega visualization.  The as_view() method
    accepts the following arguments:

      preamble
      model
      model_attr
      vega_class    
    """
    template = "cdh/simple_interface.html"
    model = None
    vega_class = None
    model_attr = None
    preamble = None

    def render(self, request):        
        w = VegaWidget(vega_class=self.vega_class, preamble=self.preamble)
        retval = w.render("", getattr(self.get_object(), self.model_attr))
        return mark_safe(retval)
    
    def get(self, request, *argv, **argd):
        return render(request, self.template, {"content" : self.render(request)})
    

class TabView(SingleObjectMixin, View):
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
        super(TabView, self).__init__(*argv, **argd)        

    def get_object(self):
        try:
            return SingleObjectMixin.get_object(self)
        except:
            return None
        
    def get_context_data(self, request, from_htmx, obj_perms, *argv, **argd):
        retval = super(TabView, self).get_context_data(*argv, **argd)
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
                        #"hx_target" : "#{}".format(self.form_id),
                        #"hx_swap" : "outerHTML",
                        "hx_swap" : "none",
                        "hx_post" : request.path_info,
                        #"hx_select" : "#top_level_content",
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
                        #reverse("{}:{}_detail".format(obj._meta.app_label, obj._meta.model_name), args=(obj.id,)),
                        #"hx_select" : "#top_level_content",
                    }
                )
            retval["content"] = self.render(request)
            retval["prefix"] = self.prefix
            return retval

        
    def render_tab(self, request, tab, obj, index):
        url = reverse(tab["url"], args=(obj.id,))
        return """
        <div id="{prefix}_{index}_tabdescription">{description}</div>
        <div id="{prefix}_{index}_tabcontent" hx-get="{url}" hx-trigger="intersect" hx-select="#top_level_content > *" hx-swap="outerHTML">
        </div>
        """.format(
            prefix=self.prefix,
            index=index,
            url=url,
            description=tab.get("description", "")
        )
    
    def render(self, request):
        self.prefix = "prefix_{}".format(slugify(request.path_info))
        obj = self.get_object()        
        controls = [
            """
            <li class="nav-item" role="presentation">
            <button class="nav-link cdh-tab-button" id="{prefix}_{index}_control" data-bs-toggle="tab" data-bs-target="#{prefix}_{index}_content" type="button" role="tab" aria-controls="{prefix}_{index}_content" aria-selected="false">{title}</button>
            </li>
            """.format(
                prefix=self.prefix,
                index=i,
                title=tab["title"]
            ) for i, tab in enumerate(self.tabs)]
        contents = [
            """
            <div class="tab-pane fade" id="{prefix}_{index}_content" role="tabpanel" aria-labelledby="{prefix}_{index}_control">
            {content}
            </div>
            """.format(
                prefix=self.prefix,
                index=i,
                content=self.render_tab(request, tab, obj, i)
            ) for i, tab in enumerate(self.tabs)]
        return mark_safe(
            """
            <div id="{prefix}_tabs">
            <ul class="nav nav-tabs cdh-nav-tabs" id="{prefix}_controls" role="tablist">
            {controls}
            </ul>
            <div class="tab-content" id="{prefix}_contents">
            {contents}
            </div>
            </div>
            """.format(
                prefix=self.prefix,
                controls="\n".join(controls),
                contents="\n".join(contents),
            )
        )
    
    def get(self, request, *argv, **argd):
        from_htmx = request.headers.get("Hx-Request", False) and True
        obj = self.get_object()
        obj_perms = [x.split("_")[0] for x in (get_perms(request.user, obj) if obj else [])]
        ctx = self.get_context_data(request, from_htmx, obj_perms)
        ctx["path"] = request.path_info
        ctx["object"] = obj
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
        #if from_htmx:
        #    resp = HttpResponse()
        resp.headers["HX-Trigger"] = """{{"cdhEvent" : {{"type" : "delete", "app" : "{app}", "model" : "{model}", "id" : "{id}"}}}}""".format(
            app=self.model._meta.app_label,
            model=self.model._meta.model_name,
            id=obj_id
        )
        print("Deleted an instance of {} and redirecting to {}".format(self.model, resp))        
        return resp
        
        
class AccordionView(View):
    """
    An AccordionView renders its "children" as siblings in a Bootstrap accordion component.
    The as_view() method accepts the following arguments:

      preamble
      model
      children

    Where "children" can either be a list whose entries are dictionaries with fields:

      title
      url

    or a dictionary with fields:

      model
      url
      create_url (optional)

    In the latter case, the dictionary is expanded to get the "actual" children corresponding
    to objects of the model visible to the current user, along with an additional child for
    creating a new object should the user have permission.

    An accordion should only allow a single child to be expanded at any given time, and should
    preserve state across page refresh/other navigation.

    Custom HTMX signals should produce the following behaviors:

      "deleted{app}{model}{id}": remove the corresponding instance wherever it occurs, if it was
                                 active, set it's preceding sibling to active if it exists.
      "created{app}{model}{id}": refresh all accordions based on the model, set current active
                                 item to the corresponding new entry.
      "updated{app}{model}{id}": refresh all children based on the instance
    
    """
    children = None
    content = None
    model = None
    template = "cdh/simple_interface.html"
    preamble = None

    def __init__(self, children, *argv, **argd):
        super(AccordionView, self).__init__(*argv, **argd)
        self.children = children

    def get_object(self):
        try:
            return SingleObjectMixin.get_object(self)
        except:
            return None

    # def deletion_reactivity(self, request, child):
    #     if "instance" in child:
    #         return """
    #         hx-trigger="deleted{app}{model}{id} from:body"
    #         hx-swap="delete"
    #         hx-target="#{prefix}_{id}_accordionitem"
    #         hx-get="{url}"
    #         id="{prefix}_{id}"
    #         """.format(
    #             app=child["instance"]._meta.app_label.replace("_", ""),
    #             model=child["instance"]._meta.model_name,
    #             id=child["instance"].id,
    #             prefix=self.prefix,
    #             url=request.path_info
    #         )
    #     else:
    #         return ""
        
    # def update_reactivity(self, request, child):
    #     if "instance" in child:
    #         return """
    #         hx-trigger="updated{app}{model}{id} from:body"
    #         hx-swap="outerHTML"
    #         hx-target="#{prefix}_{id}_accordionitem"
    #         hx-select="#{prefix}_{id}_accordionitem"
    #         hx-get="{url}"
    #         """.format(
    #             app=child["instance"]._meta.app_label.replace("_", ""),
    #             model=child["instance"]._meta.model_name,
    #             id=child["instance"].id,
    #             prefix=self.prefix,
    #             url=request.path_info,                
    #         )
    #     else:
    #         return ""

    # def creation_reactivity(self, request, child):
    #     if "model" in child:
    #         return """
    #         hx-trigger="created{app}{model} from:body"
    #         hx-swap="outerHTML"
    #         hx-target="#{prefix}_accordion"
    #         hx-select="#{prefix}_accordion"
    #         hx-get="{url}"
    #         """.format(
    #             app=child["model"]._meta.app_label.replace("_", ""),
    #             model=child["model"]._meta.model_name,
    #             prefix=self.prefix,
    #             url=request.path_info,                                
    #             # url=reverse(
    #             #     "{}:{}_list".format(
    #             #         child["model"]._meta.app_label,
    #             #         child["model"]._meta.model_name
    #             #     )
    #             # )
    #         )           


    #     else:
    #         return ""
        
    def render_child(self, request, child, index):
        if "instance" in child and "url" in child:
            url = reverse(child["url"], args=(child["instance"].id,))
        elif "url" in child:
            url = reverse(child["url"], args=())
        else:
            raise Exception("Unknown accordion child spec: {}".format(child))
        return """
        <div id="{prefix}_{id}_accordionchildcontent" hx-get="{url}" hx-trigger="intersect" hx-select="#top_level_content > *" hx-swap="outerHTML">
        </div>
        """.format(
            prefix=self.prefix,
            url=url,
            id=child["instance"].id if "instance" in child else "nonobject{}".format(index)
        )

    def expand_children(self, request):
        """
        Interpretations of the "children" argument passed to the constructor:

        1. dictionary with "model" and "url" fields and no "object":
           
        """
        retval = []
        if isinstance(self.children, dict):
            if "url" in self.children and "model" in self.children and "instance" not in self.children:
                retval = [
                    {
                        "title" : str(obj),
                        "instance" : obj,
                        "url" : self.children["url"]                        
                    } for obj in get_objects_for_user(
                        request.user,
                        klass=self.children["model"],
                        perms=["view_{}".format(self.children["model"]._meta.model_name)]
                    )
                ]
                #print(obj_perms, model_perms)
                #perms = get_perms(request.user, self.children["model"])
                #print(request.user, self.children["model"], perms)
                #actions = set([x.split("_")[0] for x in perms])
                if request.user.id != None and "create_url" in self.children:                
                    retval.append(
                        {
                            "title" : """
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-plus-circle" viewBox="0 0 16 16">
  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
  <path d="M8 4a.5.5 0 0 1 .5.5v3h3a.5.5 0 0 1 0 1h-3v3a.5.5 0 0 1-1 0v-3h-3a.5.5 0 0 1 0-1h3v-3A.5.5 0 0 1 8 4z"/>
</svg>
                            """,
                            "url" : self.children["create_url"]
                        }
                    )
        elif isinstance(self.children, list):
            for child in self.children:
                retval.append(
                    {
                        "title" : child["title"],
                        "url" : child["url"]
                    }
                )
        return retval
        
    def render(self, request):
        self.prefix = "prefix_{}".format(slugify(request.path_info))
        expanded_children = self.expand_children(request)
        accordion_content = [
            """
            <div class="accordion-item" id="{prefix}_{id}_accordionitem" aria-labelledby="{prefix}_title" model="{model_name}" app="{app_label}" obj_id="{obj_id}">
              <div class="accordion-header" id="{prefix}_{id}_header">
                <button class="accordion-button cdh-accordion-button collapsed" data-bs-toggle="collapse" type="button" aria-expanded="false" data-bs-target="#{prefix}_{id}_content" id="{prefix}_{id}_button" aria-controls="{prefix}_{id}_content">
                  {title}
                </button>
              </div>
              <div class="accordion-collapse collapse w-95 ps-4" id="{prefix}_{id}_content" aria-labelledby="{prefix}_{id}_header" data-bs-parent="#{prefix}_accordion">
                {content}
              </div>
            </div>
            """.format(
                prefix=self.prefix,
                id=child["instance"].id if "instance" in child else "nonobject{}".format(i),
                obj_id=child["instance"].id if "instance" in child else "",
                app_label=child["instance"]._meta.app_label if "instance" in child else "",
                model_name=child["instance"]._meta.model_name if "instance" in child else "",
                title=child["title"],
                content=self.render_child(request, child, i),
                deletion_reactivity="", #self.deletion_reactivity(request, child),
                update_reactivity="" #self.update_reactivity(request, child)
            ) for i, child in enumerate(expanded_children)]

        if isinstance(self.children, dict) and "model" in self.children:
            update_mechanism = """
            hx-get="{url}" hx-select="#{prefix}_accordion" hx-trigger="deleted{model}, updated{model}, created{model}"
            """.format(
                prefix=self.prefix,
                model=self.model._meta.model_name,
                url=request.path_info
            )
            #update_mechanism = ""
        else:
            update_mechanism = ""
        return mark_safe(
            """            
            <div class="accordion" id="{prefix}_accordion" {update_mechanism}>
              <div {creation_reactivity} id="{prefix}_accordion_itemcreation">
              </div>
              {accordion_content}
            </div>
            """.format(
                preamble=self.preamble if self.preamble else "",
                prefix=self.prefix,
                accordion_content="\n".join(accordion_content),
                update_mechanism=update_mechanism,
                creation_reactivity="" #self.creation_reactivity(request, self.children),
            )
        )
        
    def get(self, request, *argv, **argd):
        return render(request, self.template, {"content" : self.render(request), "preamble" : self.preamble})


class CdhSelectView(SingleObjectMixin, View):
    template_name = "cdh/simple_interface.html"
    model = None
    child_model = None
    relationship = None
    child_name_field = None
    child_url = None
    preamble = None
    
    def render(self, request):
        prefix = "selection_{}".format(slugify(request.path_info))
        obj = self.get_object()
        children = self.child_model.objects.filter(**{self.relationship : obj}).select_related()[0:1000]
        first = children[0]
        return mark_safe(
            """
            <select class="cdh-select">
            {options}
            </select>
            <div id="{prefix}_documentview" hx-get="{url}" hx-trigger="intersect" hx-select="#top_level_content > *" hx-swap="innerHTML">
            </div>
            """.format(
                prefix=prefix,
                id=obj.id,
                url=reverse(self.child_url, args=(first.id,)),
                options="\n".join(
                    [
                        """<option id="{prefix}_{index}" hx-get="{url}" hx-target="#{prefix}_documentview" hx-trigger="select" hx-swap="innerHTML" hx-select="#top_level_content" value="{prefix}_{index}">{name}</option>""".format(
                            url=reverse(self.child_url, args=(c.id,)),
                            name=str(c),
                            prefix=prefix,
                            index=i
                        ) for i, c in enumerate(children)
                    ]
                )
            )
        )

    def get(self, request, *argv, **argd):
        return render(request, self.template_name, {"content" : self.render(request), "preamble" : self.preamble})
    
    
def slide_page(request, page):    
    context = {
        "page" : page,
        "slides" : page.slides.filter(active=True),
        "public" : [
            ("about", "About"),
            ("people", "People"),
            ("resources", "Resources"),
            ("events", "Events"),
            ("opportunities", "Opportunities"),
        ],
        "private" : [
            ("primary_sources", "Primary sources"),
            ("topic_modeling", "Topic modeling"),
        ],
    }
    return render(request, 'cdh/slide_page.html', context)


def index(request):
    slidepages = models.SlidePage.objects.filter(name="news")    
    if len(slidepages) == 0:
        slidepage = models.SlidePage(name="news")
        slidepage.save()
    else:
        slidepage = slidepages[0]
    return slide_page(request, slidepage)


def slide_detail(request, sid):
    context = {
        "slide" : models.Slide.objects.get(id=sid)
    }
    return render(request, 'cdh/slide_detail.html', context)


def people(request):
    faculty = User.objects.filter(groups__name="faculty")
    postdocs = User.objects.filter(groups__name="postdoc")
    students = User.objects.filter(groups__name="student")
    affiliates = User.objects.filter(groups__name="affiliate")
    context = {
        "categories" : {
            "Faculty" : sorted(faculty, key=lambda x : x.last_name),
            "Post-doctoral fellows" : sorted(postdocs, key=lambda x : x.last_name),
            "Current and Past Students" : sorted(students, key=lambda x : x.last_name),
        }
    }
    return render(request, 'cdh/people.html', context)


def research(request):
    slidepages = models.SlidePage.objects.filter(name="research")
    if len(slidepages) == 0:
        slidepage = models.SlidePage(name="research")
        slidepage.save()
    else:
        slidepage = slidepages[0]
    return slide_page(request, slidepage)


def calendar(request):
   context = {
   }
   return render(request, 'cdh/calendar.html', context)


def about(request):
    context = {
    }
    return render(request, 'cdh/about.html', context)

