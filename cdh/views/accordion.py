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
    model = None
    template_name = "cdh/snippets/accordion.html"
    preamble = None
    ordering = "created_at"

    def setup(self, request, *argv, **argd):
        self.pk = argd.get("pk", None)
        super(AccordionView, self).setup(request, *argv, **argd)
    
    def __init__(self, children, *argv, **argd):
        super(AccordionView, self).__init__(*argv, **argd)
        self.children = children

    def get_object(self):
        try:
            return self.model.objects.get(id=self.pk) #SingleObjectMixin.get_object(self)
        except:
            return None

    def get_context_data(self, *argv, **argd):
        ctx = super(AccordionView, self).get_context_data(*argv, **argd)
        ctx["items"] = self.expand_children(self.request)
        ctx["accordion_url"] = self.request.path_info
        return ctx
        
    def expand_children(self, request):
        retval = []
        if isinstance(self.children, dict):
            if "url" in self.children and "model" in self.children and "object" not in self.children:
                qs = self.children["model"].objects
                if "relation" in self.children:
                    qs = qs.filter(**{self.children["relation"] : self.get_object().id})
                if "filter" in self.children:
                    qs = qs.filter(**self.children["filter"])
                user_viewable = [
                    (o, get_perms(self.request.user, o)) for o in get_objects_for_user(
                        self.request.user,
                        klass=qs,
                        perms=["view_{}".format(self.children["model"]._meta.model_name)],
                    ).all()
                ]
                user_ids = [o.id for o, p in user_viewable]
                anon_viewable = [
                    (o, get_perms(self.request.user, o)) for o in get_objects_for_user(
                        get_anonymous_user(),
                        klass=qs,
                        perms=["view_{}".format(self.children["model"]._meta.model_name)],
                    ) if o.id not in user_ids
                ]
                # the following requires postgres?
                #viewable = user_viewable + anon_viewable #user_viewable.union(anon_viewable)
                app_label = self.model._meta.app_label
                model_name = self.model._meta.model_name
                retval = [
                    {
                        "title" : str(obj),
                        "object" : obj,
                        "url" : self.children["url"],
                        "model_name" : obj._meta.model_name,
                        "app_label" : obj._meta.app_label,
                        "can_edit" : True,
                        "can_delete" : True,
                        "can_manage_permissions" : True,
                        "detail_url" : "{}:{}_detail".format(app_label, model_name),
                        "edit_url" : "{}:{}_edit".format(obj._meta.app_label, obj._meta.model_name),
                        "create_url" : "{}:{}_create".format(obj._meta.app_label, obj._meta.model_name),
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
        print(retval)
        return retval
        
    def get(self, request, *argv, **argd):
        ctx = self.get_context_data()
        return self.render_to_response(ctx)
