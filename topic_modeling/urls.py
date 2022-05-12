from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from . import views
from . import models

app_name = "topic_modeling"
urlpatterns = [
    path('', views.collection_list, name="index"),
    path('collection/', views.collection_list, name="collection_list"),
    path('collection/<int:cid>/', views.collection_detail, name="collection_detail"),
    path('document/<int:did>/', views.document_detail, name="document_detail"),
    path('topic_model/', views.topic_model_list, name="topic_model_list"),
    path('topic_model/<int:mid>/', views.topic_model_detail, name="topic_model_detail"),
    path('lexicon/', views.lexicon_list, name="lexicon_list"),
    path('lexicon/<int:lid>/', views.lexicon_detail, name="lexicon_detail"),
    path('output/', views.output_list, name="output_list"),
    path('output/<int:oid>/', views.output_detail, name="output_detail"),
    path('wordcloud/<int:mid>/<int:tid>/', views.wordcloud, name="topic_model_wordcloud"),
    path('vega_topics/<int:mid>/<int:tid>/', views.vega_topics, name="vega_topics"),
]

