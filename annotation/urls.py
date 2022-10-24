from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.shortcuts import redirect, render
from .models import Batch, Project
import turkle.urls
from .views import shadow_index


def simple(request):
    return redirect("/annotation/")
        

urlpatterns = [

    path(
        'shadow_index/',
        shadow_index,
        name="shadow_index"
    ),
    path(
        '',
        TemplateView.as_view(
            template_name="cdh/template_pack/accordion.html",
            extra_context={
                "items" : [
                    {"title" : "Annotate", "name" : "shadow_index", "is_model" : False, "is_object" : False},
                    {"title" : "Manage", "name" : "manage", "is_model" : False, "is_object" : False},
                ]
            }
        ),
        name="manage"
    ),

    path(
        'manage/',
        TemplateView.as_view(
            template_name="cdh/template_pack/accordion.html",
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
    path("turkle/", simple),
    path("turkle/", include('turkle.urls', namespace="turkle")),
]
