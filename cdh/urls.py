import logging
from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.views import PasswordResetView
from django.contrib import admin
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.urls import path
from django.conf import settings
from django.contrib.auth.models import Group
from django.urls import re_path, include
from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django_registration.backends.activation.views import RegistrationView
from django.conf.urls.static import static
from rest_framework.schemas import get_schema_view
from rest_framework.routers import DefaultRouter
from rest_framework.viewsets import ModelViewSet
from rest_framework.serializers import ModelSerializer
from guardian.shortcuts import assign_perm, get_anonymous_user
from .settings import MEDIA_URL, MEDIA_ROOT, STATIC_URL, STATIC_ROOT, BUILTIN_PAGES, APPS, DEBUG
from .forms import UserCreateForm
from .views import PermissionsView, SlidesView, MarkdownView, SparqlView, MaterialView
from .models import Slide, ResearchArtifact, CdhModel, Documentation, Event, Calendar, Rule
from .viewsets import AtomicViewSet
from .routers import CdhRouter
from .serializers import ResearchArtifactSerializer
from primary_sources.viewsets import MaterialViewSet


logger = logging.getLogger(__name__)


User = get_user_model()


class CustomPasswordResetView(PasswordResetView):
    @method_decorator(csrf_protect)
    def dispatch(self, *argv, **argd):
        if self.extra_email_context == None:
            self.extra_email_context = {"request" : argv[0]}
        else:
            self.extra_email_context["request"] = argv[0]
        return super(CustomPasswordResetView, self).dispatch(*argv, **argd)


router = CdhRouter()
for k, v in apps.app_configs.items():
    for model in v.get_models():
        if issubclass(model, CdhModel) and model != Documentation:
            mtn = model.model_title_name()
            router.register(
                model._meta.model_name,
                AtomicViewSet.for_model(
                    model,
                ),
                basename=model._meta.model_name
            )
router.register("user", AtomicViewSet.for_model(User, exclude_={"username" : "AnonymousUser"}), basename="user")
router.register("documentation", AtomicViewSet.for_model(Documentation), basename="documentation")
router.register("rule", AtomicViewSet.for_model(Rule), basename="rule")
router.register("calendar", AtomicViewSet.for_model(Calendar), basename="calendar")
router.register("material", MaterialViewSet, basename="material")


app_name = "cdh"
urlpatterns = [

    path(
        '',
        TemplateView.as_view(
            template_name="cdh/base.html",
            extra_context={
                "include" : "api:slide-list",
                "style" : "slideshow",
                "image_field" : "image",
                "content_field" : "article"
            }
        ),
        name="index"
    ),
    path(
        'about/',
        TemplateView.as_view(
            template_name="cdh/about.html"
        ),
        name="about"
    ),
    path(
        "wiki/",
        include("wiki.urls"),
        name="wiki"
    ),
    path(
        'people/',
        TemplateView.as_view(
            template_name="cdh/base.html",
            extra_context={"include" : "api:user-list"}
        ),
        name="people"
    ),
    path(
        'research/',
        TemplateView.as_view(
            template_name="cdh/base.html",
            extra_context={
                "include" : "api:researchartifact-list",
                "create" : {
                    "model" : ResearchArtifact,
                    "serializer" : ResearchArtifactSerializer
                }
            }
        ),
        name="researchartifact_list"
    ),
    
    # account-related
    path('accounts/register/',
        RegistrationView.as_view(
            form_class=UserCreateForm,
        ),
        name='django_registration_register',
    ),
    path('accounts/password_reset/', CustomPasswordResetView.as_view()),    
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),

    # end-points for dedicated special purposes
    path(
        "markdown/",
        MarkdownView.as_view(),
        name="markdown"
    ),
    path(
        "sparql/",
        SparqlView.as_view(),
        name="sparql"
    ),
    path(
        "materials/<str:prefix>/<str:name>/",
        MaterialView.as_view(),
        name="material"
    ),
    path(
        'permissions/<str:app_label>/<str:model>/<int:pk>/',
        PermissionsView.as_view(),        
        name="permissions"
    ),    
    path('calendar/', include('schedule.urls')),
    
    # api-related
    path("api/", include((router.urls, "api"))),
    path('openapi/', get_schema_view(
        title="CDH",
        description="API for various aspects of the JHU Center for Digital Humanities",
        version="1.0.0",
    ), name='openapi-schema'),
] + [
    
    # each app has its own set of urls
    path("{}/".format(k), include("{}.urls".format(k))) for k, v in APPS.items()
]


if DEBUG:
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
    urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
