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
from cdh.views import AccordionView, CdhView
#from . import views
#from turkle.admin import admin_site, BatchAdmin, ProjectAdmin
from turkle.models import Batch, Project
import turkle.urls



urlpatterns = [
    #path('', views.index, name="index"),

    path(
        '',
        AccordionView.as_view(
            children=[
                {
                    "title" : "Annotate",
                    "url" : "turkle:index",
                },
                {
                    "title" : "Manage",
                    "url" : "project_list",
                }
            ]
        ),
        name="index"
    ),
    path("turkle/", include('turkle.urls')),
    path(
        'project/list/',
        AccordionView.as_view(
            children={
                "model" : Project,
                "url" : "project_detail",
                "create_url" : "project_create"
            },
            model=Project,
        ),
        name="project_list"
    ),

    path(
        'project/create/',
        CdhView.as_view(
            model=Project,
            fields=["name"], #"collection", "topic_count", "lowercase", "max_context_size", "maximum_documents", "passes"],
            can_create=True,
            initial={},
        ),
        name="project_create"
    ),
    path(
        'project/<int:pk>/',
        CdhView.as_view(
            model=Project,
            fields=["name"],
            can_delete=True
        ),
        name="project_detail"
    ),


]
