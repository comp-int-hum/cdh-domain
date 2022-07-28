from datetime import datetime
from django.forms import ModelForm, modelform_factory, FileField
from django.template.engine import Engine
from django.template import Context
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

from django.views.generic.base import TemplateView, TemplateResponseMixin, ContextMixin
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views.generic import DetailView
from django.views.generic.edit import CreateView, DeleteView, UpdateView, DeletionMixin, ModelFormMixin, ProcessFormView
from django.views import View
from django.contrib.auth.models import Group
from django.core.cache import cache
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_users_with_perms, get_groups_with_perms, remove_perm
from guardian.forms import UserObjectPermissionsForm, GroupObjectPermissionsForm

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

template_engine = Engine.get_default()

logger = logging.getLogger("django")


def cdh_cache_method(method):
    def cached_method(*argv, **argd):
        obj = argv[0]
        key = "{}_{}_{}_{}".format(obj._meta.app_label, obj._meta.model_name, obj.id, method.__name__)
        timestamp_key = "TIMESTAMP_{}_{}_{}_{}".format(obj._meta.app_label, obj._meta.model_name, obj.id, method.__name__)
        cache_ts = cache.get(timestamp_key)
        obj_ts = obj.modified_at
        if cache_ts == None or cache_ts < obj_ts:
            logger.info("cache miss for key '{}'".format(key))
            retval = method(*argv, **argd)
            cache.set(timestamp_key, obj_ts, timeout=None)
            cache.set(key, retval, timeout=None)
            return retval
        else:
            logger.info("cache hit for key '{}'".format(key))
            return cache.get(key)
    return cached_method


def cdh_cache_function(func):
    raise Exception("cdh_cache_function not implemented yet!")
    def cached_func(*argv, **argd):
        return func(*argv, **argd)
    return cached_func


class IdMixin(object):
    
    def __init__(self, *argv, **argd):
        super(IdMixin, self).__init__(*argv, **argd)
        self.random_suffix = random_token(argd.get("random_length", 6))

    @property
    def sid(self):
        if getattr(self, "object", None) != None:
            model_properties = [
                self.object._meta.app_label,
                self.object._meta.model_name,
                self.object.id
            ]
        
        elif getattr(self, "model", None) != None:
            model_properties = [
                self.model._meta.app_label,
                self.model._meta.model_name
            ]
        else:
            return None
        return "_".join([str(x) for x in model_properties])

    @property
    def uid(self):
        return "{}_{}".format(self.sid, self.random_suffix)
    

class CdhView(IdMixin, DeletionMixin, UpdateView):
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

      "{app}_{model}_{pk}_deleted":
      "{app}_{model}_":
      "updated{app}{model}{pk}":

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
    buttons = None
    can_delete = False
    can_update = False
    can_create = False
    object = None
    fields = []
    preamble = None
    widgets = None
    
    def __init__(self, *argv, **argd):        
        super(CdhView, self).__init__(*argv, **argd)

    def get_object(self):
        try:
            return super(CdhView, self).get_object()
        except:
            return None
        
    def get_context_data(self, request, *argv, **argd):
        self.object = self.get_object()
        
        user_perms = get_users_with_perms(self.object, with_group_users=False, attach_perms=True) if self.object else {}
        group_perms = get_groups_with_perms(self.object, attach_perms=True) if self.object else {}
        
        ctx = super(CdhView, self).get_context_data(*argv, **argd)
        ctx["from_htmx"] = request.headers.get("Hx-Request", False) and True
        ctx["request"] = request
        ctx["object"] = self.object
        ctx["uid"] = self.uid
        ctx["sid"] = self.sid
        
        obj_perms = [x.split("_")[0] for x in (get_perms(request.user, self.object) if self.object else [])]
        model_perms = [x.split("_")[0] for x in (get_perms(request.user, self.model) if self.model else [])]

        if self.buttons:
            ctx["buttons"] = self.buttons
        elif self.can_create and request.user.username != "AnonymousUser":
            ctx["buttons"] = [
                {
                    "label" : "Create",
                    "style" : "primary",
                    "hx_swap" : "none",
                    "hx_post" : request.path_info,
                }
            ]
        else:
            ctx["buttons"] = []
            if self.can_update and "change" in obj_perms:
                ctx["buttons"].append(
                    {
                        "label" : "Save",
                        "style" : "primary",
                        "hx_target" : "#{}".format(self.uid),
                        "hx_swap" : "none",
                        "hx_post" : request.path_info,
                    }                    
                )
                ctx["user_permissions_options"] = [(u, [p.split("_")[0] for p in user_perms.get(u, [])]) for u in User.objects.all()]
                ctx["group_permissions_options"] = [(g, [p.split("_")[0] for p in group_perms.get(g, [])]) for g in Group.objects.all()]
                ctx["perms"] = ["delete", "view", "change"]
            if self.can_delete and "delete" in obj_perms:
                ctx["buttons"].append(
                    {
                        "label" : "Delete",
                        "style" : "danger",
                        "hx_confirm" : "Are you sure you want to delete this object and any others derived from it?",
                        "hx_target" : "#{}".format(self.uid),
                        "hx_swap" : "none",
                        "hx_delete" : request.path_info,
                    }
                )
        ctx["preamble"] = self.preamble
        return ctx
        
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
                    widgets = self.widgets if self.widgets else None
            return AugmentedForm
    
    def get(self, request, *argv, **argd):
        ctx = self.get_context_data(request)
        self.initial["created_by"] = request.user
        print(
            "GET to {} with HX-Trigger={} and HX-Request={}".format(
                request.path_info,
                request.headers.get("HX-Trigger"),
                request.headers.get("HX-Request")
            )
        )
        ctx["form"] = self.get_form_class()(
            instance=self.object,
            initial=None if self.object else self.initial
        )
        state = getattr(self.object, "state", None)
        if state == "PR":
            return render(request, "cdh/async_processing.html", ctx)
        elif state == "ER":
            return render(request, "cdh/async_error.html", ctx)
        else:
            return self.render_to_response(ctx)

    def create(self, request, *argv, **argd):
        if self.create_lambda:
            obj, resp = self.create_lambda(self, request, *argv, **argd)
        else:
            obj = self.get_form_class()(request.POST).save()                
            resp = HttpResponse() #HttpResponseRedirect(obj.get_absolute_url())
        assign_perm("{}.view_{}".format(self.model._meta.app_label, self.model._meta.model_name), request.user, obj)
        assign_perm("{}.delete_{}".format(self.model._meta.app_label, self.model._meta.model_name), request.user, obj)
        assign_perm("{}.change_{}".format(self.model._meta.app_label, self.model._meta.model_name), request.user, obj)
        obj.created_by = request.user
        obj.save()
        resp.headers["HX-Trigger"] = """{{"cdhEvent" : {{"event_type" : "create", "app_label" : "{app_label}", "model_name" : "{model_name}", "pk" : "{pk}"}}}}""".format(
            app_label=self.model._meta.app_label,
            model_name=self.model._meta.model_name,
            pk=obj.id
        )
        print("Created an instance of {}".format(self.model))
        print(resp.headers)
        return resp

    def update(self, request, ctx, *argv, **argd):
        if self.update_lambda:
            resp = self.update_lambda(request, *argv, **argd)
        else:
            form = self.get_form_class()(request.POST, request.FILES, instance=self.object)
            if not form.is_valid():
                return render(form) ###
            if form.has_changed():
                self.object = form.save()
            resp = HttpResponse() #Redirect(obj.get_absolute_url())
        for ptype in ["user", "group"]:
            for option, _ in ctx.get("{}_permissions_options".format(ptype), []):
                for perm in ctx.get("perms", []):
                    if str(option.id) in request.POST.getlist("{}_{}".format(ptype, perm), []):
                        to_add = "{}_{}".format(perm, option._meta.model_name)
                        assign_perm("{}_{}".format(perm, self.model._meta.model_name), option, self.object)
                    else:
                        to_remove = "{}_{}".format(perm, option._meta.model_name)
                        remove_perm("{}_{}".format(perm, self.model._meta.model_name), option, self.object)

        resp.headers["HX-Trigger"] = """{{"cdhEvent" : {{"event_type" : "update", "app_label" : "{app_label}", "model_name" : "{model_name}", "pk" : "{pk}"}}}}""".format(
            app_label=self.model._meta.app_label,
            model_name=self.model._meta.model_name,
            pk=self.object.id
        )
        print("Updated {} instance {} and redirecting to {}".format(self.model, self.object, resp))
        print(resp.headers)            
        return resp
        
    def post(self, request, *argv, **argd):
        ctx = self.get_context_data(request)
        print(
            "Handling POST to {} with HX-Trigger={} and HX-Request={}".format(
                request.path_info,
                request.headers.get("HX-Trigger"),
                request.headers.get("HX-Request")
            )
        )
        if self.object:
            return self.update(request, ctx, *argv, **argd)
        else:
            return self.create(request, ctx, *argv, **argd)

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
        pk = obj.id
        if self.delete_lambda:
            resp = self.delete_lambda(request, *argv, **argd)
        else:
            
            obj.delete()
            resp = HttpResponse()
            #resp = HttpResponseRedirect(reverse("{}:{}_list".format(obj._meta.app_label, obj._meta.model_name)))
        #if from_htmx:
        
        resp.headers["HX-Trigger"] = """{{"cdhEvent" : {{"event_type" : "delete", "app_label" : "{app_label}", "model_name" : "{model_name}", "pk" : "{pk}"}}}}""".format(
            app_label=self.model._meta.app_label,
            model_name=self.model._meta.model_name,
            pk=pk
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
    

class TabView(IdMixin, SingleObjectMixin, View):
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
        self.object = self.get_object()
        retval = super(TabView, self).get_context_data(*argv, **argd)
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
            retval["prefix"] = self.uid
            return retval
        
    # def render_tab(self, request, tab, obj, index):
    #     url = reverse(tab["url"], args=(obj.id,))
    #     return """
    #     <div id="{prefix}_{index}_tabdescription">{description}</div>
    #     <div id="{prefix}_{index}_tabcontent" hx-get="{url}" hx-trigger="intersect" hx-select="#top_level_content > *" hx-swap="outerHTML">
    #     </div>
    #     """.format(
    #         prefix=self.uid, #prefix,
    #         index=index,
    #         url=url,
    #         description=tab.get("description", "")
    #     )
    
    def render(self, request):
        content = template_engine.get_template("cdh/snippets/tabs.html").render(
            Context(
                {
                    "tabs" : self.tabs,
                    "uid" : self.uid,
                    "sid" : self.sid,
                    "instance" : self.get_object()
                }
            )
        )
        return mark_safe(content)

        # #self.prefix = "prefix_{}".format(slugify(request.path_info))
        # obj = self.get_object()        
        # controls = [
        #     """
        #     <li class="nav-item" role="presentation">
        #     <button class="nav-link cdh-tab-button" id="{prefix}_{index}_control" data-bs-toggle="tab" data-bs-target="#{prefix}_{index}_content" type="button" role="tab" aria-controls="{prefix}_{index}_content" aria-selected="false">{title}</button>
        #     </li>
        #     """.format(
        #         prefix=self.uid,
        #         index=i,
        #         title=tab["title"]
        #     ) for i, tab in enumerate(self.tabs)]
        # contents = [
        #     """
        #     <div class="tab-pane fade" id="{prefix}_{index}_content" role="tabpanel" aria-labelledby="{prefix}_{index}_control">
        #     {content}
        #     </div>
        #     """.format(
        #         prefix=self.uid,
        #         index=i,
        #         content=self.render_tab(request, tab, obj, i)
        #     ) for i, tab in enumerate(self.tabs)]
        # return mark_safe(
        #     """
        #     <div id="{prefix}_tabs">
        #     <ul class="nav nav-tabs cdh-nav-tabs" id="{prefix}_controls" role="tablist">
        #     {controls}
        #     </ul>
        #     <div class="tab-content" id="{prefix}_contents">
        #     {contents}
        #     </div>
        #     </div>
        #     """.format(
        #         prefix=self.uid,
        #         controls="\n".join(controls),
        #         contents="\n".join(contents),
        #     )
        # )
    
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
        
        
class AccordionView(IdMixin, TemplateResponseMixin, ContextMixin, View):
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

    def get_context_data(self, request, *argv, **argd):
        ctx = super(AccordionView, self).get_context_data(*argv, **argd)
        ctx["sid"] = self.sid
        ctx["uid"] = self.uid
        ctx["content"] = self.render(request)
        ctx["preamble"] = self.preamble
        return ctx
        
    def expand_children(self, request):
        retval = []
        if isinstance(self.children, dict):
            if "url" in self.children and "model" in self.children and "instance" not in self.children:
                retval = [
                    {
                        "title" : str(obj),
                        "instance" : obj,
                        "url" : self.children["url"],
                        "model_name" : obj._meta.model_name,
                        "app_label" : obj._meta.app_label
                    } for obj in get_objects_for_user(
                        request.user,
                        klass=self.children["model"],
                        perms=["view_{}".format(self.children["model"]._meta.model_name)],
                    ).order_by("created_at")
                ]
                if request.user.id != None and "create_url" in self.children:                
                    retval.append(
                        {
                            "create_url" : self.children["create_url"]
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
        content = template_engine.get_template("cdh/snippets/accordion.html").render(
            Context(
                {
                    "items" : self.expand_children(request),
                    "uid" : self.uid,
                    "sid" : self.sid,
                    "accordion_url" : request.path_info
                }
            )
        )
        return mark_safe(content)
        
    def get(self, request, *argv, **argd):
        #print(render(request, self.template, self.get_context_data(request)).content)
        return render(request, self.template, self.get_context_data(request))



class CdhSelectView(IdMixin, SingleObjectMixin, View):
    template_name = "cdh/simple_interface.html"
    model = None
    related_model = None
    relationship = None
    child_name_field = None
    related_url = None
    preamble = None
    limit = 100
    
    def render(self, request):
        prefix = self.uid #"selection_{}".format(slugify(request.path_info))
        obj = self.get_object()
        related_objects = self.related_model.objects.filter(**{self.relationship : obj}).select_related()[0:self.limit]
        content = template_engine.get_template("cdh/snippets/select.html").render(
            Context(
                {
                    "options" : related_objects,
                    "uid" : self.uid,
                    "sid" : self.sid,
                    "related_url" : self.related_url,
                }
            )
        )
        return mark_safe(content)

        # first = children[0]
        # return mark_safe(
        #     """
        #     <select class="cdh-select">
        #     {options}
        #     </select>
        #     <div id="{prefix}_documentview" hx-get="{url}" hx-trigger="intersect" hx-select="#top_level_content > *" hx-swap="innerHTML">
        #     </div>
        #     """.format(
        #         prefix=prefix,
        #         id=obj.id,
        #         url=reverse(self.child_url, args=(first.id,)),
        #         options="\n".join(
        #             [
        #                 """<option id="{prefix}_{index}" hx-get="{url}" hx-target="#{prefix}_documentview" hx-trigger="select" hx-swap="innerHTML" hx-select="#top_level_content" value="{prefix}_{index}">{name}</option>""".format(
        #                     url=reverse(self.child_url, args=(c.id,)),
        #                     name=str(c),
        #                     prefix=prefix,
        #                     index=i
        #                 ) for i, c in enumerate(children)
        #             ]
        #         )
        #     )
        # )

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

