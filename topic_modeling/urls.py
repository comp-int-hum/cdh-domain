import os
import os.path
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from .models import Lexicon, TopicModel
from cdh.models import Documentation

app_name = "topic_modeling"
urlpatterns = [
    path(
        '',
        TemplateView.as_view(
            template_name="cdh/accordion.html",
            extra_context={
                "items" : [
                    TopicModel,
                    Lexicon,
                    # {
                    #     "title" : "Labeled text",
                    #     "name" : "api:topicmodel-list"
                    # }
                ],
                "uid" : "1",
            }
        ),
        name="index"
    )
]
