from django.urls import path
from django.views.generic import TemplateView
from .models import PrimarySource, Query


app_name = "primary_sources"
urlpatterns = [
    path(
        "",
        TemplateView.as_view(
            template_name="cdh/accordion.html",
            extra_context={
                "items" : [
                    PrimarySource,
                    Query
                ]
            }
        ),
        name="index"
    )
]
