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
from . import views


app_name = "primary_sources"
urlpatterns = [
    path('', views.dataset_list, name="dataset_list"),
    path('dataset/<int:did>/', views.dataset_detail, name="dataset_detail"),
    path('dataset_ontology_graph/<int:dataset_id>/', views.dataset_ontology_graph, name="dataset_ontology_graph"),
]
