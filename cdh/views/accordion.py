from django.shortcuts import render, get_object_or_404
from django.views.generic.base import TemplateView, TemplateResponseMixin, ContextMixin
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views import View
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_anonymous_user
from django.utils.safestring import mark_safe
from django.template.engine import Engine
from django.template import Context
from django.contrib.contenttypes.models import ContentType
from cdh.models import Documentation
from .mixins import NestedMixin
from .base import BaseView

template_engine = Engine.get_default()


class AccordionView(NestedMixin, TemplateResponseMixin, BaseView):
    children = None
    content = None
    parent_model = None
    parent_relation = None
    template_name = "cdh/snippets/accordion.html"
    preamble = None
    ordering = "created_at"
    can_delete = True
    can_edit = True
    can_create = False
    filters = None
    url = None
    
    def setup(self, request, *argv, **argd):
        self.pk = argd.get("pk", None)
        super(AccordionView, self).setup(request, *argv, **argd)
    
    def __init__(self, *argv, **argd):
        super(AccordionView, self).__init__(*argv, **argd)

    def get_context_data(self, *argv, **argd):
        ctx = super(AccordionView, self).get_context_data(*argv, **argd)
        ctx["items"] = self.expand_children(self.request)
        #ctx["accordion_url"] = self.request.path_info
        ctx["can_create"] = self.can_create
        ctx["model"] = self.model
        #ctx["url"] = self.url if self.url else "{}:{}_detail".format(self.app_label, self.model_name)
        return ctx

    def get_parent(self, *argv, **argd):
        return self.parent_model.objects.get(id=self.pk)
    
    def get_queryset(self, *argv, **argd):
        if self.model:            
            qs = self.model.objects
            if self.parent_relation and self.parent_model:                
                qs = qs.filter(**{self.parent_relation : self.get_parent()})
            if self.filters:
                qs = qs.filter(**self.filters)
            return qs
        else:
            return []
    
    def expand_children(self, request):
        retval = []

        #retval = 
        # elif isinstance(self.children, dict):
        #     if "url" in self.children and "model" in self.children and "object" not in self.children:
        #         qs = self.children["model"].objects
        #         if "relation" in self.children:
        #             qs = qs.filter(**{self.children["relation"] : self.get_object().id})
        if not self.children:
            qs = self.get_queryset()
            user_viewable = [
                (o, get_perms(self.request.user, o)) for o in get_objects_for_user(
                    self.request.user,
                    klass=qs,
                    perms=["view_{}".format(self.model_name)],
                ).all()
            ]
            user_ids = [o.id for o, p in user_viewable]
            anon_viewable = [
                (o, get_perms(self.request.user, o)) for o in get_objects_for_user(
                    get_anonymous_user(),
                    klass=qs,
                    perms=["view_{}".format(self.model_name)],
                ) if o.id not in user_ids
            ]
            # the following requires postgres?
            #viewable = user_viewable + anon_viewable #user_viewable.union(anon_viewable)
            retval = [
                {
                    "title" : str(obj),
                    "object" : obj,
                    "url" : self.url if self.url else "{}:{}_detail".format(self.app_label, self.model_name), #children["url"],
                    "model_name" : self.model_name,
                    "app_label" : self.app_label,
                    "can_edit" : self.can_edit,
                    "can_delete" : True,
                    "can_manage_permissions" : True,
                    "detail_url" : "{}:{}_detail".format(self.app_label, self.model_name),
                    "edit_url" : "{}:{}_edit".format(self.app_label, self.model_name),
                    #"create_url" : "{}:{}_create".format(obj._meta.app_label, obj._meta.model_name),
                } for obj, perms in anon_viewable + user_viewable
            ]
        elif isinstance(self.children, list):
            for child in self.children:
                if isinstance(child, dict):
                    item = child
                    model = child.get("model")
                else:
                    item = {
                    }
                    model = child
                if model:
                    app_label = model._meta.app_label
                    model_name = model._meta.model_name
                    item["url"] = item.get("url", "{}:{}_list".format(app_label, model_name))
                    item["title"] = item.get("title", model._meta.verbose_name_plural.title())
                    item["model_name"] = model._meta.verbose_name.title()
                    item["model"] = model
                    item["edit_url"] = item.get("edit_url", "{}:{}_edit".format(app_label, model_name))
                    item["detail_url"] = item.get("detail_url", "{}:{}_detail".format(app_label, model_name))
                    item["create_url"] = item.get("create_url", "{}:{}_create".format(app_label, model_name))
                    if self.request.user.has_perm("{}.add_{}".format(app_label, model_name)):
                        item["can_create"] = True
                        
                    if self.request.user.has_perm("{}.delete_{}".format(app_label, model_name)):
                        item["can_manage_permissions"] = True
                        item["can_delete"] = True

                    if self.request.user.has_perm("{}.change_{}".format(app_label, model_name), self.object):
                        item["can_edit"] = True
                retval.append(item)
        return retval
        
    def get(self, request, *argv, **argd):
        ctx = self.get_context_data()
        return self.render_to_response(ctx)
