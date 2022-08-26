import logging
from django.contrib.auth.models import Group
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.apps import apps
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView, DeletionMixin, ModelFormMixin, ProcessFormView
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_users_with_perms, get_groups_with_perms, remove_perm
from cdh.models import User
from .mixins import ButtonsMixin, NestedMixin
from .base import BaseView


class PermissionsView(BaseView):

    def __init__(self, *argv, **argd):
        super(PermissionsView, self).__init__(*argv, **argd)
    
    def dispatch(self, request, app_label, model, pk, *argv, **argd):
        self.request = request
        self.app = apps.get_app_config(app_label)
        self.model = self.app.get_model(model)
        self.object = self.model.objects.get(id=pk)
        return super(PermissionsView, self).dispatch(request, *argv, **argd)

    def get_context_data(self, *argv, **argd):
        ctx = super(PermissionsView, self).get_context_data(*argv, **argd)
        ctx["user_permissions_options"] = [(u, [p.split("_")[0] for p in self.user_perms.get(u, [])]) for u in User.objects.all()]
        ctx["group_permissions_options"] = [(g, [p.split("_")[0] for p in self.group_perms.get(g, [])]) for g in Group.objects.all()]
        ctx["perms"] = ["delete", "view", "change"]
        return ctx
        
    def get(self, request, *argv, **argd):
        ctx = self.get_context_data()
        return render(request, "cdh/snippets/permissions.html", ctx)

    def post(self, request, *argv, **argd):
        ctx = self.get_context_data()
        for ptype in ["user", "group"]:
            for option, _ in ctx.get("{}_permissions_options".format(ptype), []):
                for perm in ctx.get("perms", []):
                    if str(option.id) in request.POST.getlist("{}_{}".format(ptype, perm), []):
                        to_add = "{}_{}".format(perm, option._meta.model_name)
                        assign_perm("{}_{}".format(perm, self.model._meta.model_name), option, self.object)
                    else:
                        to_remove = "{}_{}".format(perm, option._meta.model_name)
                        remove_perm("{}_{}".format(perm, self.model._meta.model_name), option, self.object)
        return HttpResponseRedirect(request.path_info)
