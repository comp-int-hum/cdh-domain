import re
import logging
from django.utils.module_loading import import_string
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.contenttypes.models import ContentType
from django.template.loader import get_template, TemplateDoesNotExist
from rest_framework.viewsets import ModelViewSet
from rest_framework import exceptions, status
from rest_framework.fields import empty
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.schemas.openapi import AutoSchema
from guardian.shortcuts import get_perms, get_objects_for_user, get_anonymous_user
from .renderers import CdhTemplateHTMLRenderer
from .negotiation import CdhContentNegotiation
from .serializers import DocumentationSerializer
from .models import Documentation, Slide


logger = logging.getLogger(__name__)


class AtomicViewSet(ModelViewSet):
    content_negotiation_class = CdhContentNegotiation
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer, CdhTemplateHTMLRenderer]
    detail_template_name = "cdh/atomic.html"
    list_template_name = "cdh/accordion.html"
    slideshow_template_name = "cdh/slideshow.html"
    model = None
    exclude = {}
    
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
        accordion_header_template_name_ = "{}/{}_accordion_header.html".format(app_name, model_name.lower())
        try:
            accordion_header_template_ = get_template(accordion_header_template_name_)
        except TemplateDoesNotExist as e:
            accordion_header_template_ = False
        class GeneratedViewSet(cls):
            schema = AutoSchema(
                tags=[model_name],
                component_name=model_name,
                operation_id_base=model_name
            )
            model = model_
            exclude = exclude_
            serializer_class = serializer_class_ if serializer_class_ else import_string("{}.serializers.{}Serializer".format(app_name, class_name))
            accordion_header_template_name = accordion_header_template_name_ if accordion_header_template_ else None
        for i, (name, props) in enumerate(extra_actions):
            def callback(self, request, pk=None, name=name):
                obj = self.get_object()
                args = {k : v[0] if isinstance(v, list) else v for k, v in request.data.items()}
                print(args)
                # {k : v[0] if isinstance(v, list) else v for k, v in list(request.GET.items()) + list(request.POST.items())}
                retval = getattr(obj, name)(**args)
                return Response(retval)
            callback.__name__ = name        
            setattr(GeneratedViewSet, name, action(url_name=name, url_path=name, **props)(callback))
        return GeneratedViewSet

    def get_queryset(self):
        perms = "{}_{}".format(
            "delete" if self.action == "destroy" else "add" if self.action == "create" else "change" if self.action in ["update", "partial_update"] else "view" if self.action in ["retrieve", "list"] else "view",
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
        if self.kwargs[lookup_url_kwarg] == "None":
            return None
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        obj = get_object_or_404(queryset, **filter_kwargs)        
        return obj

    def initialize_request(self, request, *argv, **argd):
        retval = super(AtomicViewSet, self).initialize_request(request, *argv, **argd)
        self.template_name = self.list_template_name if self.action == "list" else self.detail_template_name
        self.request = request
        self.uid = self.request.headers.get("uid", "1")
        # style (currently) can be: "tab", "accordion", "modal", "slideshow", or None/""
        self.style = self.request.headers.get("style")
        self.mode = self.request.headers.get("mode")
        if self.style == "slideshow":
            self.template_name = self.slideshow_template_name
        self.method = self.request.method
        self.from_htmx = self.request.headers.get("Hx-Request", False) and True
        if self.model:
            self.app_label = self.model._meta.app_label
            self.model_name = self.model._meta.model_name
            self.model_perms = ["add"] if self.request.user.has_perm("{}.add_{}".format(self.app_label, self.model_name)) else []
        return retval

    def get_renderer_context(self, *argv, **argd):
        context = super(AtomicViewSet, self).get_renderer_context(*argv, **argd)
        context["mode"] = self.mode
        context["model"] = self.model
        context["model_name"] = self.model._meta.verbose_name.title()
        context["model_name_plural"] = self.model._meta.verbose_name_plural.title()
        context["model_perms"] = self.model_perms
        context["uid"] = self.uid
        context["style"] = self.style
        if self.style == "slideshow":
            context["image_field"] = self.request.headers.get("image_field")
            context["content_field"] = self.request.headers.get("content_field")
            context["slide_model"] = Slide
        if self.detail:
            obj = self.get_object()
            if obj != None:
                context["serializer"] = self.get_serializer(obj)
                context["object"] = obj
            else:
                context["serializer"] = self.get_serializer()
        elif self.action == "create":
            context["serializer"] = self.get_serializer()
        elif not self.detail:
            context["serializer"] = self.get_serializer()
            context["items"] = self.get_queryset()
            context["accordion_header_template_name"] = self.accordion_header_template_name
        else:
            raise Exception("Incoherent combination of detail/action on AtomicViewSet")
        logger.info("Accepted renderer: %s", self.request.accepted_renderer)
        context["viewset"] = self
        return context

    def list(self, request):
        logger.info("List invoked by %s", request.user)
        if request.accepted_renderer.format == "cdh":
            context = self.get_renderer_context()
            return Response(context)
        else:
            return super(AtomicViewSet, self).list(request)

        
    # this should return response for HTML too
    def create(self, request):
        logger.info("Create %s invoked by %s", self.model._meta.model_name, request.user)
        if request.user.has_perm("{}.add_{}".format(self.model._meta.app_label, self.model._meta.model_name)):
            logger.info("Permission verified")
            try:
                retval = super(AtomicViewSet, self).create(request)
            except Exception as e:
                logging.warn("Exception in create method of AtomicViewSet: %s", e)
                raise e
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
        obj = self.get_object()
        if obj == None:
            ser = self.get_serializer()
        else:
            ser = self.get_serializer(obj)
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
            retval.headers["HX-Trigger"] = """{{"cdhEvent" : {{"event_type" : "update", "model_class" : "{app_label}-{model_name}", "object_class" : "{app_label}-{model_name}-{pk}"}}}}""".format(
                app_label=self.model._meta.app_label,
                model_name=self.model._meta.model_name,
                pk=pk
            )                
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
