import logging
from django.urls import path
from django.views.generic import TemplateView
from .models import MachineLearningModel


logger = logging.getLogger(__name__)


# ** potential use for ?customized=true
#
# TORCHSERVE_MANAGEMENT_ADDRESS
# options /
# post /models
# put /models/{name}
# get /models/{name} /models/{name}/{version} /models/{name}/all
# delete /models/{name}/{version}
# get /models
# put /models/{name}/{version}/set-default
#
# TORCHSERVE_INFERENCE_ADDRESS
# options / (list inference APIs)
# 
# TORCHSERVE_METRICS_ADDRESS
# TBD: get /metrics?...


app_name = "machine_learning"


urlpatterns = [
    path(
        '',
        TemplateView.as_view(
            template_name="cdh/accordion.html",
            extra_context={"items" : [MachineLearningModel]}
        ),
        name="index"
    ),
]
