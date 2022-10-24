import logging
from django.urls import path
from django.views.generic import TemplateView
from .models import MachineLearningModel


logger = logging.getLogger(__name__)


app_name = "machine_learning"


urlpatterns = [
    path(
        '',
        TemplateView.as_view(
            template_name="cdh/template_pack/accordion.html",
            extra_context={"items" : [MachineLearningModel]}
        ),
        name="index"
    ),
]
