from django.contrib.auth import get_user_model
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django_registration.backends.activation.views import RegistrationView
from django.conf.urls.static import static
from rest_framework import routers, serializers, viewsets
from rest_framework.schemas import get_schema_view
from .settings import MEDIA_URL, MEDIA_ROOT, STATIC_URL, STATIC_ROOT, BUILTIN_PAGES, APPS, DEBUG
from .forms import UserForm
from .views import BaseView, PermissionsView, AccordionView, TabsView, SlidesView, MarkdownView, SparqlView, MaterialView
from .viewsets import BaseViewSet
from .models import Slide, ResearchArtifact


User = get_user_model()




class SlideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Slide
        fields = "__all__"

class SlideViewSet(viewsets.ModelViewSet):
    queryset = Slide.objects.all()
    serializer_class = SlideSerializer

router = routers.DefaultRouter()
router.register("slide", SlideViewSet)

app_name = "cdh"
urlpatterns = [

    
    # landing page/slides
    path(
        '',
        SlidesView.as_view(model=Slide),
        name="index"
    ),
    path(
        'slide/list/',
        AccordionView.as_view(
            model=Slide,
            preamble="""
            """,
            children={
                "model" : Slide,
                "url" : "slide_detail",
                "create_url": "slide_create"
            }
        ),
        name="slide_list"        
    ),
    path(
        'slide/<int:pk>/',
        BaseView.as_view(
            model=Slide,
            fields=["image", "article"],
            can_update=True,
            can_delete=True
        ),
        name="slide_detail"
    ),    
    path(
        'slide/create/',
        BaseView.as_view(
            model=Slide,
            fields=["article", "image"],
            can_create=True
        ),
        name="slide_create"
    ),    

    
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
        BaseView.as_view(
            model=User,
            can_manage=False,
            can_update=True,
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
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),


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
        BaseView.as_view(
            model=ResearchArtifact,
            can_delete=True,
            can_update=True,
            fields=["name", "authors", "author_freetext", "description"]
        ),
        name="researchartifact_detail"
    ),    
    path(
        'researchartifact/create/',
        BaseView.as_view(
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
    #path("api/", include(router.urls)),
    #path('api-auth/', include('rest_framework.urls')),
    path('openapi/', get_schema_view(
        title="CDH",
        description="API for various aspects of the JHU Center for Digital Humanities",
        version="1.0.0"
    ), name='openapi-schema'),
    
] + [path("{}/".format(k), include("{}.urls".format(k))) for k, v in APPS.items()]


if DEBUG:
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
    urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
