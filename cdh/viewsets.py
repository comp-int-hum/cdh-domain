import logging
from django.forms import ModelForm, Field
from django.db.models.fields.related import ForeignKey
from django.utils.module_loading import import_string
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.contenttypes.models import ContentType
from rest_framework.viewsets import ModelViewSet, GenericViewSet, ViewSet
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.serializers import ModelSerializer, HiddenField, CurrentUserDefault, HyperlinkedModelSerializer, HyperlinkedIdentityField, ReadOnlyField
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer, BrowsableAPIRenderer
from rest_framework.schemas.openapi import AutoSchema
from rest_framework.permissions import DjangoObjectPermissions
from django.utils.safestring import mark_safe
from .models import Documentation
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_users_with_perms, get_groups_with_perms, remove_perm, get_anonymous_user
from .renderers import CdhTemplateHTMLRenderer
from .negotiation import CdhContentNegotiation
from .serializers import DocumentationSerializer


logger = logging.getLogger(__name__)


class AtomicViewSet(ModelViewSet):
    content_negotiation_class = CdhContentNegotiation
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer, CdhTemplateHTMLRenderer]
    detail_template_name = "cdh/atomic.html"
    list_template_name = "cdh/accordion.html"
    model = None
    exclude = {}
    
    def initial(self, request, *argv, **argd):
        return super(AtomicViewSet, self).initial(request, *argv, **argd)

    def handle_exception(self, exc, *argv, **argd):
        logger.error("Viewset exception %s", exc)
        return super(AtomicViewSet, self).handle_exception(exc, *argv, **argd)    

    def initialize_request(self, request, *argv, **argd):
        return super(AtomicViewSet, self).initialize_request(request, *argv, **argd)
    
    @classmethod
    def for_model(cls, model_, create_form_class_=None, edit_form_class_=None, view_form_class_=None, serializer_class_=None, exclude_={}):
        extra_actions = []
        for slot in dir(model_):
            method = getattr(model_, slot, None)
            if isinstance(method, type(cls.initial)):
                props = getattr(method, "action_properties", None)
                if props != None:
                    extra_actions.append((slot, props))
            elif isinstance(method, property):
                props = getattr(method.fget, "action_properties", None)
                if props != None:
                    extra_actions.append((slot, props))        
        model_name = model_._meta.model_name.title()
        app_name = model_._meta.app_label
        class_name = model_._meta.verbose_name.title().replace(" ", "")
        # class GeneratedViewForm(ModelForm):
        #     class Meta:
        #         model = model_
        #         fields = "__all__"
        #         exclude = ["name"]
        # class GeneratedSerializer(HyperlinkedModelSerializer):
        #     url = HyperlinkedIdentityField(view_name="api:{}-detail".format(model_name.lower()), lookup_field="id", lookup_url_kwarg="pk")
        #     created_by = HiddenField(
        #         default=CurrentUserDefault()
        #     )
        #     class Meta:
        #         model = model_
        #         fields = [f.name for f in model_._meta.fields if not isinstance(f, ForeignKey)] + ["url", "created_by"]
        #         depth = 0
        # class GeneratedCreateForm(ModelForm):
        #     class Meta:
        #         model = model_
        #         fields = "__all__"
        # class GeneratedEditForm(ModelForm):
        #     class Meta:
        #         model = model_
        #         fields = "__all__"
        #         exclude = ["name"]
        class GeneratedViewSet(cls):
            schema = AutoSchema(
                tags=[model_name],
                component_name=model_name,
                operation_id_base=model_name
            )
            model = model_
            exclude = exclude_
            serializer_class = import_string("{}.serializers.{}Serializer".format(app_name, class_name))                
        for name, props in extra_actions:
            def callback(self, request, pk=None):
                obj = self.get_object()
                args = {k : v[0] if isinstance(v, list) else v for k, v in list(request.GET.items()) + list(request.POST.items())}
                retval = getattr(obj, name)(**args)
                return Response(retval)
            callback.__name__ = name
            setattr(GeneratedViewSet, name, action(**props)(callback))
        return GeneratedViewSet

    def get_queryset(self):
        perms = "{}_{}".format(
            "delete" if self.action == "destroy" else "add" if self.action == "create" else "change" if self.action in ["update", "partial_update"] else "view" if self.action in ["retrieve", "list"] else None,
            self.model._meta.model_name
        )
        
        return (get_objects_for_user(get_anonymous_user(), perms=perms, klass=self.model) | get_objects_for_user(self.request.user, perms=perms, klass=self.model)).exclude(**self.exclude)

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)
        return obj

    def initialize_request(self, request, *argv, **argd):
        retval = super(AtomicViewSet, self).initialize_request(request, *argv, **argd)
        self.template_name = self.list_template_name if self.action == "list" else self.detail_template_name
        self.request = request
        self.uid = self.request.headers.get("uid", "0")
        # style (currently) can be: "tab", "accordion", "modal", or None
        self.style = self.request.headers.get("style")
        self.method = self.request.method
        self.from_htmx = self.request.headers.get("Hx-Request", False) and True
        if self.model:
            self.app_label = self.model._meta.app_label
            self.model_name = self.model._meta.model_name
            self.model_perms = ["add"] if self.request.user.has_perm("{}.add_{}".format(self.app_label, self.model_name)) else []
        return retval

    def get_serializer_variant(self, obj, variant):
        serializer = self.get_serializer(obj) if obj else self.get_serializer()
        keep = getattr(serializer.Meta, "{}_fields".format(variant), [])
        serializer.fields = {field_name : field for field_name, field in serializer.fields.items() if field_name in keep}
        
        for field in serializer.fields:
            if variant == "edit":
                serializer.fields[field].style["editable"] = True
                
        return serializer
    
    def get_renderer_context(self, *argv, **argd):
        context = super(AtomicViewSet, self).get_renderer_context(*argv, **argd)
        context["model"] = self.model
        context["model_name"] = self.model._meta.verbose_name.title()
        context["model_name_plural"] = self.model._meta.verbose_name_plural.title()
        context["model_perms"] = self.model_perms
        context["uid"] = self.uid
        context["style"] = self.style
        if self.detail:
            obj = self.get_object()
            context["view_serializer"] = self.get_serializer_variant(obj, "view")
            if obj.get_change_perm() in get_perms(self.request.user, obj):
                context["edit_serializer"] = self.get_serializer_variant(obj, "edit")
                for field in context["edit_serializer"].fields:
                    npf = getattr(context["edit_serializer"].fields[field], "nested_parent_field", None)
                    if npf != None:
                        context["edit_serializer"].fields[field].style["parent_id"] = getattr(obj, npf).id
            for field in context["view_serializer"].fields:
                context["view_serializer"].fields[field].style["object"] = obj
                context["view_serializer"].fields[field].style["method"] = self.request.method
            context["object"] = obj
        elif self.action == "create":
            context["serializer"] = self.get_serializer_variant(None, "create")
        else:
            context["create_serializer"] = self.get_serializer_variant(None, "create")
            for field in context["create_serializer"].fields:
                context["create_serializer"].fields[field].style["editable"] = True
            context["items"] = self.get_queryset()
        view_name = self.request.path_info
        content_type = ContentType.objects.get_for_model(context["model"]) if context.get("model", None) else None
        object_id = getattr(context.get("object", None), "id", None)
        # docs = Documentation.objects.filter(
        #     view_name=view_name,
        #     content_type=content_type,
        #     object_id=object_id
        # )
        # context["documentation_model"] = Documentation
        # if docs.count() > 1:
        #     raise Exception("More than one Documentation object for view_name={}/content_type={}/object_id={}".format(view_name, content_type, object_id))
        # elif docs.count() == 1:
        #     #context["documentation"] = docs[0]
        #     context["documentation_serializer"] = DocumentationSerializer(docs[0], context={"request" : self.request})
        #     context["documentation_object"] = docs[0]
        # else:
        #     context["documentation_serializer"] = DocumentationSerializer(
        #         instance = Documentation(
        #             **{
        #                 "name" : "/".join([str(x) for x in [view_name.rstrip("/"), context.get("model_name", None), object_id] if x]),
        #                 "view_name" : view_name,
        #                 "content_type" : content_type,
        #                 "object_id" : object_id
        #             }
        #             ),
        #         context={"request" : self.request}
        #     )
        #     #context["documentation_serializer"].is_valid()

        logger.info("Accepted renderer: %s", self.request.accepted_renderer)
        return context

    def list(self, request):
        logger.info("List invoked by %s", request.user)
        if request.accepted_renderer.format == "cdh":
            context = self.get_renderer_context()
            return Response(context)
        else:
            return super(AtomicViewSet, self).list(request)

    def create(self, request):
        logger.info("Create %s invoked by %s", self.model._meta.model_name, request.user)
        if request.user.has_perm("{}.add_{}".format(self.model._meta.app_label, self.model._meta.model_name)):
            logger.info("Permission verified")
            retval = super(AtomicViewSet, self).create(request)
            pk = retval.data["id"]
            if request.accepted_renderer.format == "cdh":
                retval = HttpResponse()
                retval.headers["HX-Trigger"] = """{{"cdhEvent" : {{"event_type" : "create", "model_class" : "{app_label}-{model_name}", "object_class" : "{app_label}-{model_name}-{pk}", "model_url" : "{model_url}"}}}}""".format(
                    app_label=self.model._meta.app_label,
                    model_name=self.model._meta.model_name,
                    pk=pk,
                    model_url=self.model.get_list_url()
                )                
            return retval
        else:
            raise exceptions.PermissionDenied(
                detail="{} does not have permission to create {}".format(
                    request.user,
                    self.model._meta.model_name
                ),
                code=status.HTTP_403_FORBIDDEN
            )

    def retrieve(self, request, pk=None):
        logger.info("Retrieve invoked by %s", request.user)
        ser = self.get_serializer(self.get_object())
        return Response(ser.data)

    def destroy(self, request, pk=None):
        logger.info("Delete invoked by %s for %s", request.user, pk)
        retval = super(AtomicViewSet, self).destroy(request, pk)        
        retval = HttpResponse()
        if request.accepted_renderer.format == "cdh":
            retval.headers["HX-Trigger"] = """{{"cdhEvent" : {{"event_type" : "delete", "model_class" : "{app_label}-{model_name}", "object_class" : "{app_label}-{model_name}-{pk}"}}}}""".format(
                app_label=self.model._meta.app_label,
                model_name=self.model._meta.model_name,
                pk=pk
            )
        return retval
        
    def update(self, request, pk=None, partial=False):
        logger.info("Update invoked by %s for %s", request.user, pk)
        if self.model.get_change_perm() in get_perms(request.user, self.get_object()):
            logger.info("Permission verified")
            retval = super(AtomicViewSet, self).update(request, pk)
            return retval
        else:
            raise exceptions.PermissionDenied(
                detail="{} does not have permission to change {} object {}".format(
                    request.user,
                    self.model._meta.model_name,
                    pk
                ),
                code=status.HTTP_403_FORBIDDEN
            )
