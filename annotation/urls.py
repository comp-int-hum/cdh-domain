"""cdh URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.shortcuts import redirect, render
#from cdh.views import AccordionView, AtomicView, generate_default_urls
from .models import Batch, Project
import turkle.urls
#from .forms import ProjectForm, BatchForm
from .views import shadow_index

def simple(request):
    return redirect("/annotation/")
        

urlpatterns = [

    path(
        'shadow_index/',
        shadow_index,
        name="shadow_index"
    ),
    
    # path(
    #     '',
    #     AccordionView.as_view(
    #         children=[
    #             {
    #                 "title" : "Annotate",
    #                 "url" : "shadow_index",
    #             },
    #             {
    #                 "title" : "Manage",
    #                 "url" : "manage"
    #             }
    #         ]
    #     ),
    #     name="index"
    # ),
    path(
        '',
        TemplateView.as_view(
            template_name="cdh/accordion.html",
            extra_context={
                "items" : [
                    {"title" : "Annotate", "name" : "shadow_index"},
                    {"title" : "Manage", "name" : "manage"},
                ]
            }
        ),
        name="manage"
    ),

    path(
        'manage/',
        TemplateView.as_view(
            template_name="cdh/accordion.html",
            extra_context={
                "items" : [
                    Project,
                    Batch
                ],
                "uid" : "manage",
            }
        ),
        name="manage"
    ),

    
    # path(
    #     'manage/',
    #     AccordionView.as_view(
    #         children=[
    #             {
    #                 "title" : "Projects",
    #                 "url" : "project_list",
    #             },
    #             {
    #                 "title" : "Batches",
    #                 "url" : "batch_list"
    #             }
    #         ]
    #     ),
    #     name="manage"
    # ),

    # path(
    #     'project/list/',
    #     AccordionView.as_view(
    #         children={
    #             "model" : Project,
    #             "url" : "project_detail",
    #             "create_url" : "project_create"
    #         },
    #         model=Project,
    #     ),
    #     name="project_list"
    # ),

    # path(
    #     'batch/list/',
    #     AccordionView.as_view(
    #         children={
    #             "model" : Batch,
    #             "url" : "batch_detail",
    #             "create_url" : "batch_create"
    #         },
    #         model=Batch,
    #     ),
    #     name="batch_list"
    # ),
    path("turkle/", simple),
    path("turkle/", include('turkle.urls', namespace="turkle")),

    # path(
    #     'project/create/',
    #     AtomicView.as_view(
    #         model=Project,
    #         form_class=ProjectForm,
    #         #fields=["name"],
    #         can_create=True,
    #         initial={},
    #     ),
    #     name="project_create"
    # ),
    
    # path(
    #     'project/<int:pk>/',
    #     AtomicView.as_view(
    #         model=Project,
    #         form_class=ProjectForm,
    #         #fields=["name"],
    #         can_delete=True
    #     ),
    #     name="project_detail"
    # ),

    # path(
    #     'batch/create/',
    #     AtomicView.as_view(
    #         model=Batch,
    #         form_class=BatchForm,
    #         #fields=["name"],
    #         can_create=True,
    #         initial={},
    #     ),
    #     name="batch_create"
    # ),

    # path(
    #     'batch/<int:pk>/',
    #     AtomicView.as_view(
    #         model=Batch,
    #         form_class=BatchForm,
    #         #fields=["name"],
    #         can_delete=True
    #     ),
    #     name="batch_detail"
    # )
    
]
#+ generate_default_urls(
#    Batch,
#    Project
#)
