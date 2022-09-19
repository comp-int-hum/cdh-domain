import logging
from django.forms import ModelForm, Field
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView, DeletionMixin, ModelFormMixin, ProcessFormView
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_users_with_perms, get_groups_with_perms, remove_perm
from cdh.models import User
from rest_framework.views import APIView
from .mixins import ButtonsMixin, NestedMixin
from .base import BaseView

logger = logging.getLogger()


class AtomicView(NestedMixin, DeletionMixin, UpdateView, BaseView):
    template_name = "cdh/atomic.html"
    extra_fields = {}
    form_class = None
    post_lambda = None
    create_lambda = None
    delete_lambda = None
    update_lambda = None
    form_htmx = {
    }
    can_delete = False
    can_update = False
    can_create = False
    can_manage = True
    object = None
    fields = []
    preamble = None
    widgets = None
    editable = False
    exclude = ["metadata", "created_by", "state", "message", "task_id"]
    
    def __init__(self, *argv, **argd):
        super(AtomicView, self).__init__(*argv, **argd)

    def setup(self, request, *argv, **argd):
        super(AtomicView, self).setup(request, *argv, **argd)
        self.pk = argd.get("pk", None)
        self.object = self.get_object()
        self.user_perms = get_users_with_perms(self.object, with_group_users=False, attach_perms=True) if self.object else {}
        self.group_perms = get_groups_with_perms(self.object, attach_perms=True) if self.object else {}
        self.obj_perms = [x.split("_")[0] for x in (get_perms(self.request.user, self.object) if self.object else [])]
        self.model_perms = [x.split("_")[0] for x in (get_perms(self.request.user, self.model) if self.model else [])]
        
    def get_object(self):
        try:
            return self.model.objects.get(id=self.pk)
        except:
            return None

    def get_context_data(self, *argv, **argd):
        ctx = super(AtomicView, self).get_context_data(*argv, **argd)
        ctx["editable"] = self.editable
        return ctx
        
    def get_form_class(self, create=False):
        editable = self.editable and ("change" in self.obj_perms or self.object == None)
        if self.form_class:
            class DerivedForm(self.form_class):
                def __init__(sself, *argv, **argd):
                    super(DerivedForm, sself).__init__(*argv, **argd)
                    if not editable:
                        for name, field in sself.fields.items():
                            field.widget.attrs['readonly'] = 'true'
                            if name == "name":
                                field.widget.hidden = True                                
                                field.widget.attrs['hidden'] = 'true';
                class Meta:
                    model = self.model
                    fields = self.fields
                    exclude= self.exclude
                    widgets = self.widgets if self.widgets else None
            return DerivedForm
        else:
            class AugmentedForm(ModelForm):
                def __init__(sself, *argv, **argd):
                    super(AugmentedForm, sself).__init__(*argv, **argd)
                    for k, v in self.extra_fields.items():
                        if isinstance(v, tuple):
                            sself.fields[k] = v[0](**v[1])
                        else:
                            if isinstance(v, Field):
                                sself.fields[k] = v
                            else:
                                sself.fields[k] = v()
                    if not editable:
                        for name, field in sself.fields.items():
                            field.widget.attrs['readonly'] = 'true'
                            if name == "name":
                                field.widget.hidden = True
                                field.widget.attrs['hidden'] = 'true';
                class Meta:
                    model = self.model
                    fields = self.fields
                    exclude = self.exclude
                    widgets = self.widgets if self.widgets else None
            return AugmentedForm
    
    def get(self, request, *argv, **argd):
        ctx = self.get_context_data()
        self.initial["created_by"] = request.user
        if "relation" in request.GET:
            self.initial[request.GET["relation"]] = int(request.GET["pk"])
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
        self.request = request
        ctx = self.get_context_data()
        if self.create_lambda:
            form, obj = self.create_lambda(self, request, *argv, **argd)
        else:
            form = self.get_form_class(create=True)(request.POST, request.FILES)
            obj = None
        ctx["form"] = self.get_form_class()(initial=self.initial) if form.is_valid() else form
        if obj == None and form.is_valid():
            obj = form.save(commit=False)
        resp = self.render_to_response(ctx)
        if obj != None:
            obj.created_by = request.user
            obj.save()
            #for user in User.objects.all():
            #    assign_perm("{}.view_{}".format(self.model._meta.app_label, self.model._meta.model_name), user, obj)
            #assign_perm("{}.delete_{}".format(self.model._meta.app_label, self.model._meta.model_name), request.user, obj)
            #assign_perm("{}.change_{}".format(self.model._meta.app_label, self.model._meta.model_name), request.user, obj)
            
            #obj.created_by = request.user
            #obj.save()
            resp.headers["HX-Trigger"] = """{{"cdhEvent" : {{"event_type" : "create", "app_label" : "{app_label}", "model_name" : "{model_name}", "pk" : "{pk}"}}}}""".format(
                app_label=self.model._meta.app_label,
                model_name=self.model._meta.model_name,
                pk=obj.id
            )
        return resp

    def update(self, request, ctx, *argv, **argd):
        if self.update_lambda:
            resp = self.update_lambda(self, request, *argv, **argd)
        else:
            form = self.get_form_class()(request.POST, request.FILES, instance=self.object)
            if not form.is_valid():
                ctx["form"] = form
                return self.render_to_response(ctx) #form) ###
            if form.has_changed():
                self.object = form.save()

            resp = HttpResponseRedirect(request.path_info)

        resp.headers["HX-Trigger"] = """{{"cdhEvent" : {{"event_type" : "update", "app_label" : "{app_label}", "model_name" : "{model_name}", "pk" : "{pk}"}}}}""".format(
            app_label=self.model._meta.app_label,
            model_name=self.model._meta.model_name,
            pk=self.object.id
        )
        return resp
        
    def post(self, request, *argv, **argd):
        self.request = request
        ctx = self.get_context_data()
        if self.object:
            return self.update(request, ctx, *argv, **argd)
        else:
            return self.create(request, ctx, *argv, **argd)

    def delete(self, request, *argv, **argd):
        from_htmx = request.headers.get("Hx-Request", False) and True
        self.request = request
        obj = self.get_object()
        pk = obj.id
        if self.delete_lambda:
            resp = self.delete_lambda(request, *argv, **argd)
        else:            
            obj.delete()
            resp = HttpResponse()
        resp.headers["HX-Trigger"] = """{{"cdhEvent" : {{"event_type" : "delete", "app_label" : "{app_label}", "model_name" : "{model_name}", "pk" : "{pk}"}}}}""".format(
            app_label=self.model._meta.app_label,
            model_name=self.model._meta.model_name,
            pk=pk
        )
        return resp
