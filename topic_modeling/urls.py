from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from django.views.decorators.cache import cache_page
from . import views
from . import models

app_name = "topic_modeling"
urlpatterns = [
    path('', views.index, name="index"),
    path('collection/', views.collection_list, name="collection_list"),
    path('collection/<int:cid>/', views.collection_list, name="collection_detail"),
    path('document/<int:did>/', views.labeled_document_detail, name="document_detail"),
    path('labeled_collection/<int:lcid>/', views.labeled_collection_detail, name="labeled_collection_detail"),
    path('labeled_document/<int:did>/', views.labeled_document_detail, name="labeled_document_detail"),

    path('lexicon/', views.lexicon_list, name="lexicon_list"),
    path('lexicon/<int:lid>/', views.lexicon_detail, name="lexicon_detail"),
    
    path('topic_model/', views.topic_model_list, name="topic_model_list"),
    path('topic_model/<int:mid>/', views.topic_model_detail, name="topic_model_detail"),
    path('topic_model/<int:mid>/<int:tid>/', views.topic_model_topic_detail, name="topic_model_topic_detail"),

    path('labeled_collection/<int:lcid>/spatial/', views.spatial, name="spatial_distribution"),
    path('labeled_collection/<int:lcid>/temporal/', views.temporal, name="temporal_evolution"),

    path('vega_wordcloud/<int:mid>/<int:tid>/', views.vega_wordcloud, name="vega_wordcloud"),
    path('vega_spatial/<int:lcid>/', views.vega_spatial, name="vega_spatial"),
    path('vega_temporal/<int:lcid>/', views.vega_temporal, name="vega_temporal"),
]
