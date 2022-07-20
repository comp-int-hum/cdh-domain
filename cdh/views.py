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
from guardian.shortcuts import get_perms, get_objects_for_user

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
    template_name = "cdh/simple_form.html"
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

    def __init__(self, *argv, **argd):        
        return super(CdhView, self).__init__(*argv, **argd)
    
    def get_object(self):
        try:
            return super(CdhView, self).get_object()
        except:
            return None
        
    def get_context_data(self, from_htmx, model_perms, obj_perms, *argv, **argd):
        retval = super(CdhView, self).get_context_data(*argv, **argd)
        if self.buttons:
            retval["buttons"] = self.buttons
        elif self.can_create and "add" in model_perms:
            retval["buttons"] = [
                {
                    "label" : "Create",
                    "style" : "primary",
                    #"hx_swap" : "outerHTML",
                    "hx_swap" : "none",
                    "hx_post" : "1",
                    "hx_select" : "#top_level_content",
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
                        #"hx_swap" : "outerHTML",
                        "hx_swap" : "none",
                        "hx_post" : "1",
                        #"hx_select" : "#top_level_content",
                    }                    
                )
            if self.can_delete and "delete" in obj_perms:
                retval["buttons"].append(
                    {
                        "label" : "Delete",
                        "style" : "danger",
                        "hx_confirm" : "Are you sure you want to delete this object and any others derived from it?",
                        "hx_target" : "#{}".format(self.form_id),
                        "hx_swap" : "outerHTML",
                        "hx_delete" : "1",
                        "hx_select" : "#top_level_content",
                    }
                )
        retval["form_id"] = self.form_id
        retval["from_htmx"] = from_htmx
        #retval["buttons"] = [{k : v for k, v in b.items() if (not k.startswith("hx_") or from_htmx)} for b in retval.get("buttons", [])]
        return retval
        
    def form_valid(self, form):
        #print("valid")
        resp = super(CdhView, self).form_valid(form)
        #resp.headers["HX-Trigger"] = "created{}".format(self.model._meta.model_name)
        return resp

    def form_invalid(self, form):
        resp = super(CdhView, self).form_invalid(form)
        #resp.headers["HX-Trigger"] = "created{}".format(self.model._meta.model_name)
        return resp
    
    def get_form_class(self):
        if self.form_class:
            return self.form_class
        else:
            class AugmentedForm(ModelForm):
                def __init__(sself, *argv, **argd):
                    super(AugmentedForm, sself).__init__(*argv, **argd)
                    for k, v in self.extra_fields.items():                
                        sself.fields[k] = v()
                class Meta:
                    model = self.model
                    fields = self.fields
            return AugmentedForm
    
    def get(self, request, *argv, **argd):
        from_htmx = request.headers.get("Hx-Request", False) and True
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
        ctx = self.get_context_data(from_htmx, model_perms, obj_perms)
        if obj:
            ctx["form"] = self.get_form_class()(instance=obj)
        else:
            ctx["form"] = self.get_form_class()(initial=self.initial)
            
        ctx["htmx_request"] = from_htmx
        ctx["object"] = obj
        if state == "PR":
            return render(request, "cdh/async_processing.html", ctx)
        elif state == "ER":
            return render(request, "cdh/async_error.html", ctx)
        else:
            return self.render_to_response(ctx)

    def post(self, request, *argv, **argd):
        from_htmx = request.headers.get("Hx-Request", False) and True
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
                self.update_lambda(request, *argv, **argd)
            else:
                form = self.get_form_class()(request.POST, instance=obj)
                if form.has_changed():
                    form.save()
                resp = HttpResponseRedirect(obj.get_absolute_url())
            if from_htmx:
                resp.headers["HX-Trigger"] = "updated{app}{model}{id}".format(
                    app=self.model._meta.app_label.replace("_", ""),
                    model=self.model._meta.model_name,
                    id=obj.id
                )
            print("Updated {} instance {} and redirecting to {}".format(self.model, obj, resp))
            print(resp.headers)            
            return resp
        else:
            if self.create_lambda:
                resp = self.create_lambda(self, request, *argv, **argd)
            else:
                obj = self.get_form_class()(request.POST).save()                
                resp = HttpResponseRedirect(obj.get_absolute_url())
            
            if from_htmx:
                resp.headers["HX-Trigger"] = "created{app}{model}".format(
                    app=self.model._meta.app_label.replace("_", ""),
                    model=self.model._meta.model_name,
                )
            print("Created an instance of {}".format(self.model))
            print(resp.headers)
            return resp

    def delete(self, request, *argv, **argd):
        from_htmx = request.headers.get("Hx-Request", False) and True
        print(
            "DELETE to {} with HX-Trigger={} and HX-Request={}".format(
                request.path_info,
                request.headers.get("HX-Trigger"),
                request.headers.get("HX-Request")
            )
        )
        if self.delete_lambda:
            resp = self.delete_lambda(request, *argv, **argd)
        else:
            obj = self.get_object()
            obj.delete()
            resp = HttpResponseRedirect(reverse("{}:{}_list".format(obj._meta.app_label, obj._meta.model_name)))
        if from_htmx:
            resp = HttpResponse()
            resp.headers["HX-Trigger"] = "deleted{app}{model}{id}".format(
                app=self.model._meta.app_label.replace("_", ""),
                model=self.model._meta.model_name,
                id=obj.id
            )
        print("Deleted an instance of {} and redirecting to {}".format(self.model, resp))        
        return resp


class VegaView(SingleObjectMixin, View):
    template = "cdh/simple_interface.html"
    model = None
    vega_class = None
    model_attr = None
    def render(self, request):        
        w = VegaWidget(vega_class=self.vega_class)
        retval = w.render("", getattr(self.get_object(), self.model_attr))
        return mark_safe(retval)
    
    def get(self, request, *argv, **argd):
        return render(request, self.template, {"content" : self.render(request)})
    

class TabView(SingleObjectMixin, View):

    tabs = None
    model = None
    template = "cdh/simple_interface.html"
    can_delete = False
    can_update = False
    object = None
    buttons = None
    
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
                        "hx_target" : "#{}".format(self.form_id),
                        #"hx_swap" : "outerHTML",
                        "hx_swap" : "none",
                        "hx_post" : "1",
                        #"hx_select" : "#top_level_content",
                    }                    
                )
            if self.can_delete and "delete" in obj_perms:
                retval["buttons"].append(
                    {
                        "label" : "Delete",
                        "style" : "danger",
                        "hx_confirm" : "Are you sure you want to delete this object and any others derived from it?",
                        #"hx_target" : "#{prefix}_tabs", ########.format(self.prefix),
                        "hx_swap" : "none",
                        "hx_delete" : reverse("{}:{}_detail".format(obj._meta.app_label, obj._meta.model_name), args=(obj.id,)),
                        "hx_select" : "#top_level_content",
                    }
                )
            retval["content"] = self.render(request)
            return retval
            
    def render_tab(self, request, tab, obj, index):
        
        url = reverse(tab["url"], args=(obj.id,))
        return """
        <div id="{prefix}_{index}_tabcontent" hx-get="{url}" hx-trigger="intersect" hx-select="#top_level_content > *" hx-swap="outerHTML">
        </div>
        """.format(
            prefix=self.prefix,
            index=index,
            url=url
        )
    
    def render(self, request):
        self.prefix = "prefix_{}".format(slugify(request.path_info))
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

        obj = self.get_object()
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
        return render(request, self.template, ctx)


    def delete(self, request, *argv, **argd):
        from_htmx = request.headers.get("Hx-Request", False) and True
        obj = self.get_object()
        obj.delete()
        resp = HttpResponseRedirect(reverse("{}:{}_list".format(obj._meta.app_label, obj._meta.model_name)))
        if from_htmx:
            resp = HttpResponse()
            resp.headers["HX-Trigger"] = "deleted{app}{model}{id}".format(
                app=self.model._meta.app_label.replace("_", ""),
                model=self.model._meta.model_name,
                id=obj.id
            )
        print("Deleted an instance of {} and redirecting to {}".format(self.model, resp))        
        return resp
        
        

class AccordionView(View):

    children = None
    content = None
    model = None
    template = "cdh/simple_interface.html"
    
    def __init__(self, children, *argv, **argd):
        super(AccordionView, self).__init__(*argv, **argd)
        self.children = children

    def get_object(self):
        try:
            return SingleObjectMixin.get_object(self)
        except:
            return None

    def deletion_reactivity(self, request, child):
        if "instance" in child:
            return """
            hx-trigger="deleted{app}{model}{id} from:body"
            hx-swap="delete"
            hx-target="#{prefix}_{id}_accordionitem"
            hx-get="{url}"
            id="{prefix}_{id}"
            """.format(
                app=child["instance"]._meta.app_label.replace("_", ""),
                model=child["instance"]._meta.model_name,
                id=child["instance"].id,
                prefix=self.prefix,
                url=request.path_info
            )
        else:
            return ""
        
    def update_reactivity(self, request, child):
        if "instance" in child:
            return """
            hx-trigger="updated{app}{model}{id} from:body"
            hx-swap="outerHTML"
            hx-target="#{prefix}_{id}_accordionitem"
            hx-select="#{prefix}_{id}_accordionitem"
            hx-get="{url}"
            """.format(
                app=child["instance"]._meta.app_label.replace("_", ""),
                model=child["instance"]._meta.model_name,
                id=child["instance"].id,
                prefix=self.prefix,
                url=request.path_info,                
            )
        else:
            return ""

    def creation_reactivity(self, request, child):
        if "model" in child:
            return """
            hx-trigger="created{app}{model} from:body"
            hx-swap="outerHTML"
            hx-target="#{prefix}_accordion"
            hx-select="#{prefix}_accordion"
            hx-get="{url}"
            """.format(
                app=child["model"]._meta.app_label.replace("_", ""),
                model=child["model"]._meta.model_name,
                prefix=self.prefix,
                url=request.path_info,                                
                # url=reverse(
                #     "{}:{}_list".format(
                #         child["model"]._meta.app_label,
                #         child["model"]._meta.model_name
                #     )
                # )
            )           


        else:
            return ""
        
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
                    } for obj in get_objects_for_user(request.user, klass=self.children["model"], perms=["view"])
                ]
                perms = get_perms(request.user, self.children["model"])
                actions = set([x.split("_")[0] for x in perms])                
                if "add" in actions and "create_url" in self.children:
                    retval.append(
                        {
                            "title" : "+",
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
            <div class="accordion-item" id="{prefix}_{id}_accordionitem" aria-labelledby="{prefix}_title">
              <div {deletion_reactivity}>
              </div>
              <div {update_reactivity}>
              </div>
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
                title=child["title"],
                content=self.render_child(request, child, i),
                deletion_reactivity=self.deletion_reactivity(request, child),
                update_reactivity=self.update_reactivity(request, child)
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
                prefix=self.prefix,
                accordion_content="\n".join(accordion_content),
                update_mechanism=update_mechanism,
                creation_reactivity=self.creation_reactivity(request, self.children),
            )
        )
        
    def get(self, request, *argv, **argd):
        return render(request, self.template, {"content" : self.render(request)})
        
    
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
