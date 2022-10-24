from django.urls import path
from django.views.generic import TemplateView
from .models import PrimarySource, Query, Annotation


app_name = "primary_sources"
urlpatterns = [
    path(
        "",
        TemplateView.as_view(
            template_name="cdh/template_pack/accordion.html",
            extra_context={
                "items" : [
                    PrimarySource,
                    Query,
                    Annotation
                ]
            }
        ),
        name="index"
    )
]
