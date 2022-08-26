import logging
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView, DeletionMixin, ModelFormMixin, ProcessFormView
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_users_with_perms, get_groups_with_perms, remove_perm
from cdh.models import User
from rest_framework.views import APIView
from .mixins import ButtonsMixin, NestedMixin


logger = logging.getLogger()


class BaseView(ButtonsMixin, NestedMixin, DeletionMixin, UpdateView):
    # """
    # BaseView is intended as the "ground-level" view for a single CDH-related object
    # in a CRUD form.  The as_view() method accepts the following arguments:

    #   preamble
    #   model
    #   form_class
    #   fields
    #   extra_fields
    #   initial
    #   can_create
    #   can_delete
    #   can_update
    #   create_lambda: returns tuple of (object, response)
    #   delete_lambda
    #   update_lambda

    # If the created object is asynchronous and in a "processing" state, the
    # returned content will be a self-updating HTMX placeholder.  If in an "error" state,
    # a non-updating placeholder will be returned.  In both cases, any message on the
    # object will be displayed as well.

    # Created objects will default to allowing public view, with all additional permissions
    # assigned to the creator.
    # """
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
    can_manage = True
    object = None
    fields = []
    preamble = None
    widgets = None
    
    def __init__(self, *argv, **argd):
        #if "name" not in argd.get("fields", []):
        #    argd["fields"] = ["name"] + argd.get("fields", [])
        super(BaseView, self).__init__(*argv, **argd)

    def dispatch(self, request, *argv, **argd):
        self.request = request
        self.object = self.get_object()
        return super(BaseView, self).dispatch(request, *argv, **argd)
        
    def get_object(self):
        try:
            return super(BaseView, self).get_object()
        except:
            return None
        
    def get_context_data(self, *argv, **argd):
        #self.object = self.get_object()
        self.from_htmx = self.request.headers.get("Hx-Request", False) and True
        
        self.user_perms = get_users_with_perms(self.object, with_group_users=False, attach_perms=True) if self.object else {}
        self.group_perms = get_groups_with_perms(self.object, attach_perms=True) if self.object else {}
        self.obj_perms = [x.split("_")[0] for x in (get_perms(self.request.user, self.object) if self.object else [])]
        self.model_perms = [x.split("_")[0] for x in (get_perms(self.request.user, self.model) if self.model else [])]
        
        ctx = super(BaseView, self).get_context_data(*argv, **argd)
        ctx["from_htmx"] = self.request.headers.get("Hx-Request", False) and True
        ctx["request"] = self.request
        ctx["object"] = self.object
        ctx["preamble"] = self.preamble
        ctx["app_label"] = self.object._meta.app_label if self.object else None
        ctx["model_name"] = self.object._meta.model_name if self.object else None
        ctx["pk"] = self.object.id if self.object else None
        ctx["can_manage"] = self.object and "change" in self.obj_perms and self.can_manage
        return ctx
        
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        resp = super(BaseView, self).form_valid(form)
        return resp

    def form_invalid(self, form):
        resp = super(BaseView, self).form_invalid(form)
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
        self.request = request
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
            form = self.get_form_class()(request.POST, request.FILES)
            obj = None
        ctx["form"] = self.get_form_class()(initial=self.initial) if form.is_valid() else form
        if obj == None and form.is_valid():
            obj = form.save(commit=False)
        resp = self.render_to_response(ctx)
        if obj != None:
            obj.created_by = request.user
            obj.save()
            for user in User.objects.all():
                assign_perm("{}.view_{}".format(self.model._meta.app_label, self.model._meta.model_name), user, obj)
            assign_perm("{}.delete_{}".format(self.model._meta.app_label, self.model._meta.model_name), request.user, obj)
            assign_perm("{}.change_{}".format(self.model._meta.app_label, self.model._meta.model_name), request.user, obj)
            
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
                return render(form) ###
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
