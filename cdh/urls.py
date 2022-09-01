from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.views import PasswordResetView
from django.contrib import admin
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.urls import path
from django.conf import settings
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
from .forms import UserForm, PublicUserForm, PublicResearchForm
from .views import AtomicView, PermissionsView, AccordionView, TabsView, SlidesView, MarkdownView, SparqlView, MaterialView, generate_default_urls
from .models import Slide, ResearchArtifact, CdhModel, Documentation


User = get_user_model()


class CustomPasswordResetView(PasswordResetView):
    @method_decorator(csrf_protect)
    def dispatch(self, *argv, **argd):
        if self.extra_email_context == None:
            self.extra_email_context = {"request" : argv[0]}
        else:
            self.extra_email_context["request"] = argv[0]
        return super(CustomPasswordResetView, self).dispatch(*argv, **argd)


router = DefaultRouter()
for k, v in apps.app_configs.items():
    for model in v.get_models():
        if issubclass(model, CdhModel):
            class GeneratedSerializer(ModelSerializer):
                class Meta:
                    model = model
                    fields = "__all__"
            class GeneratedViewSet(ModelViewSet):
                queryset = model.objects.all()
                serializer_class = GeneratedSerializer
            router.register(model._meta.model_name, GeneratedViewSet)
                

app_name = "cdh"
urlpatterns = [
    # landing page/slides
    path(
        '',
        SlidesView.as_view(model=Slide),
        name="index"
    ),
    # path(
    #     'slide/list/',
    #     AccordionView.as_view(
    #         model=Slide,
    #         preamble="""
    #         """,
    #         children={
    #             "model" : Slide,
    #             "url" : "slide_detail",
    #             "create_url": "slide_create"
    #         }
    #     ),
    #     name="slide_list"        
    # ),
    # path(
    #     'slide/<int:pk>/',
    #     AtomicView.as_view(
    #         model=Slide,
    #         fields=["image", "article"],
    #         can_update=True,
    #         can_delete=True
    #     ),
    #     name="slide_detail"
    # ),    
    # path(
    #     'slide/create/',
    #     AtomicView.as_view(
    #         model=Slide,
    #         fields=["article", "image"],
    #         can_create=True
    #     ),
    #     name="slide_create"
    # ),    

    
    # static 'about' page
    path(
        'about/',
        TemplateView.as_view(
            template_name="cdh/about.html"
        ),
        name="about"
    ),


    # wiki
    path(
        "wiki/",
        include("wiki.urls"),
        name="wiki"
    ),
    
    
    # personnel page
    path(
        'people/',
        AccordionView.as_view(
            children=[
                {
                    "title" : "Faculty",
                    "url" : "faculty_list",
                },
                {
                    "title" : "Post-doctoral researchers",
                    "url" : "postdoc_list",
                },
                {
                    "title" : "Students",
                    "url" : "student_list",
                },
                {
                    "title" : "Affiliates",
                    "url" : "affiliate_list",
                },                
            ]
        ),
        name="people"
    ),
    path(
        "user/<int:pk>/",
        AtomicView.as_view(
            model=User,
            can_manage=False,
            can_update=True,
            form_class=PublicUserForm,
            fields=["first_name", "last_name", "title", "homepage", "photo", "description"]
        ),
        name="user_detail"
    ),
    path(
        'faculty/list/',
        AccordionView.as_view(
            model=User,
            children={
                "model" : User,
                "url" : "user_detail",
                "filter" : {"groups__name" : "faculty"}
            },
            ordering="last_name"            
        ),
        name="faculty_list"
    ),
    path(
        'postdoc/list/',
        AccordionView.as_view(
            model=User,
            children={
                "model" : User,
                "url" : "user_detail",
                "filter" : {"groups__name" : "postdoc"}
            },
            ordering="last_name"            
        ),
        name="postdoc_list"
    ),
    path(
        'student/list/',
        AccordionView.as_view(
            model=User,
            children={
                "model" : User,
                "url" : "user_detail",
                "filter" : {"groups__name" : "student"}
            },
            ordering="last_name"            
        ),
        name="student_list"
    ),
    path(
        'affiliate/',
        AccordionView.as_view(
            model=User,
            children={
                "model" : User,
                "url" : "user_detail",
                "filter" : {"groups__name" : "affiliate"}
            },
            ordering="last_name"            
        ),
        name="affiliate_list",
    ),

    
    # general permissions-management interface
    path(
        'permissions/<str:app_label>/<str:model>/<int:pk>/',
        PermissionsView.as_view(),        
        name="permissions"
    ),

    
    # account registration mechanisms
    path('accounts/register/',
        RegistrationView.as_view(
            form_class=UserForm,
        ),
        name='django_registration_register',
    ),



    # research page
    path(
        'research/',
        AccordionView.as_view(
            model=ResearchArtifact,
            preamble="""
            """,
            children={
                "model" : ResearchArtifact,
                "url" : "researchartifact_detail",
                "create_url": "researchartifact_create"
            }
        ),
        name="researchartifact_list"
    ),
    path(
        'researchartifact/<int:pk>/',
        AtomicView.as_view(
            model=ResearchArtifact,
            can_delete=True,
            can_update=True,
            form_class=PublicResearchForm,
            fields=["name", "authors", "author_freetext", "description"]
        ),
        name="researchartifact_detail"
    ),    
    path(
        'researchartifact/create/',
        AtomicView.as_view(
            model=ResearchArtifact,
            can_create=True,
            fields=["name", "authors", "author_freetext", "description"]
        ),
        name="researchartifact_create"
    ),
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
    path("api/", include(router.urls)),
    path('openapi/', get_schema_view(
        title="CDH",
        description="API for various aspects of the JHU Center for Digital Humanities",
        version="1.0.0"
    ), name='openapi-schema'),
    path('accounts/password_reset/', CustomPasswordResetView.as_view()),    
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
] + [
    path("{}/".format(k), include("{}.urls".format(k))) for k, v in APPS.items()
] + generate_default_urls(
    Slide,
    Documentation
)



if DEBUG:
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
    urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
