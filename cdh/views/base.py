import logging
import re
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic.base import TemplateView, TemplateResponseMixin, ContextMixin
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView, DeletionMixin, ModelFormMixin, ProcessFormView
from django.contrib.contenttypes.models import ContentType
from django.views import View
from cdh.models import Documentation
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_users_with_perms, get_groups_with_perms, remove_perm, get_anonymous_user
from cdh.models import User
from rest_framework.views import APIView
from .mixins import ButtonsMixin, NestedMixin


logger = logging.getLogger()


class BaseView(ContextMixin, View):
    object = None
    model = None
    obj_perms = []
    model_perms = []
    
    def setup(self, request, *argv, **argd):
        self.request = request
        self.uid = self.request.headers.get("uid", "0")
        # style (currently) can be: "tab", "accordion", "modal", or None
        self.style = self.request.headers.get("style")
        self.method = self.request.method
        self.from_htmx = self.request.headers.get("Hx-Request", False) and True
        if self.object:
            self.user_perms = get_users_with_perms(self.object, with_group_users=False, attach_perms=True)
            self.group_perms = get_groups_with_perms(self.object, attach_perms=True)
            self.obj_perms = [x.split("_")[0] for x in get_perms(self.request.user, self.object)]
        if self.model:
            self.app_label = self.model._meta.app_label
            self.model_name = self.model._meta.model_name
            self.model_perms = ["add"] if self.request.user.has_perm("{}.add_{}".format(self.app_label, self.model_name)) else []
        return super(BaseView, self).setup(request, *argv, **argd)

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        resp = super(AtomicView, self).form_valid(form)
        return resp

    def get_context_data(self, *argv, **argd):
        ctx = super(BaseView, self).get_context_data(*argv, **argd)
        # doc_search = {
        #     "view_name" : re.sub(r"\d+\/", "<int:pk>/", self.request.path_info),
        #     "content_type" : ContentType.objects.get(app_label=self.model._meta.app_label, model=self.model._meta.model_name) if self.model else None,
        #     "object_id" : self.object.id if self.object else None
        # }
        # documentations = Documentation.objects.filter(**doc_search)
        # if len(documentations) == 1:
        #     ctx["documentation"] = documentations[0]
        # elif self.request.user.is_authenticated and not (self.model and self.model._meta.app_label == "cdh" and self.model._meta.model_name == "documentation"):
        #     documentations.delete()
        #     ctx["documentation"] = Documentation.objects.create(
        #         name="Documentation for view {} of {} object {}".format(doc_search["view_name"], self.model._meta.model_name, self.object) if doc_search["object_id"] else "Documentation for view {} of model {}".format(doc_search["view_name"], self.model._meta.model_name) if doc_search["content_type"] else "Documentation for view {}".format(doc_search["view_name"]),
        #         value="",
        #         created_by=self.request.user,
        #         **doc_search
        #     )
        #     ctx["documentation"].save()
        
        # if "documentation" in ctx:
        #     ctx["can_edit_documentation"] = "change" in [p.split("_")[0] for p in get_perms(self.request.user, ctx["documentation"])]
        # ctx["from_htmx"] = self.from_htmx
        # ctx["obj_perms"] = self.obj_perms
        # ctx["model_perms"] = self.model_perms
        # if self.model:
        #     ctx["model_name"] = self.model_name
        #     ctx["app_label"] = self.app_label
        #     ctx["create_url"] = "{}:{}_create".format(self.app_label, self.model_name)
        #     ctx["edit_url"] = "{}:{}_edit".format(self.app_label, self.model_name)
        #     ctx["detail_url"] = "{}:{}_detail".format(self.app_label, self.model_name)
        #     ctx["delete_url"] = "{}:{}_list".format(self.app_label, self.model_name)
        # ctx["uid"] = self.uid
        # ctx["request"] = self.request
        # ctx["object"] = self.object
        # ctx["style"] = self.style
        print(ctx)
        return ctx
