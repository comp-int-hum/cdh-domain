from django.shortcuts import render, get_object_or_404
from django.views.generic.base import TemplateView, TemplateResponseMixin, ContextMixin
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views import View
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_users_with_perms, get_groups_with_perms, remove_perm, get_anonymous_user
from django.utils.safestring import mark_safe
from django.template.engine import Engine
from django.template import Context
from .mixins import NestedMixin


template_engine = Engine.get_default()


class AccordionView(NestedMixin, TemplateResponseMixin, ContextMixin, View):
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

    def get_context_data(self, request, *argv, **argd):
        self.object = self.get_object()
        self.request = request
        self.from_htmx = request.headers.get("Hx-Request", False) and True
        ctx = super(AccordionView, self).get_context_data(*argv, **argd)
        
        ctx["preamble"] = self.preamble
        ctx["items"] = self.expand_children(request)
        ctx["accordion_url"] = request.path_info
        ctx["model_name"] = self.model._meta.model_name if self.model else None
        ctx["app_label"] = self.model._meta.app_label if self.model else None
        return ctx
        
    def expand_children(self, request):
        retval = []
        if isinstance(self.children, dict):
            if "url" in self.children and "model" in self.children and "instance" not in self.children:
                qs = self.children["model"].objects
                print(self.children)
                if "relation" in self.children:
                    qs = qs.filter(**{self.children["relation"] : self.get_object().id})
                if "filter" in self.children:
                    qs = qs.filter(**self.children["filter"])
                user_viewable = get_objects_for_user(
                    request.user,
                    klass=qs,
                    perms=["view_{}".format(self.children["model"]._meta.model_name)],
                ).all()
                user_ids = [u.id for u in user_viewable]
                anon_viewable = [u for u in get_objects_for_user(
                    get_anonymous_user(),
                    klass=qs,
                    perms=["view_{}".format(self.children["model"]._meta.model_name)],
                ) if u.id not in user_ids]
                # the following requires postgres?
                #viewable = user_viewable + anon_viewable #user_viewable.union(anon_viewable)
                retval = [
                    {
                        "title" : str(obj),
                        "instance" : obj,
                        "url" : self.children["url"],
                        "model_name" : obj._meta.model_name,
                        "app_label" : obj._meta.app_label
                    } for obj in anon_viewable
                ] + [
                    {
                        "title" : str(obj),
                        "instance" : obj,
                        "url" : self.children["url"],
                        "model_name" : obj._meta.model_name,
                        "app_label" : obj._meta.app_label
                    } for obj in user_viewable
                ]
                    
                if request.user.id != None and "create_url" in self.children:
                    if "relation" in self.children:
                        retval.append(
                            {
                                "create_url" : self.children["create_url"],
                                "pk" : self.pk,
                                "relation" : self.children["relation"]
                            }
                        )
                    else:
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
        
    def render(self, ctx):
        content = template_engine.get_template("cdh/snippets/accordion.html").render(
            Context(ctx)
        )
        return mark_safe(content)
        
    def get(self, request, *argv, **argd):
        ctx = self.get_context_data(request)
        ctx["content"] = self.render(ctx)
        return render(request, self.template, ctx)
