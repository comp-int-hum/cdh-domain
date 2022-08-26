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
from django.http import HttpResponse, HttpResponseRedirect
from django.forms import CharField
from cdh.views import BaseView, AccordionView
from cdh.widgets import MonacoEditorWidget
from .models import MachineLearningModel
from .widgets import MachineLearningModelInteractionWidget

from django.shortcuts import render
import requests
from .tasks import load_model
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

# TORCHSERVE_INFERENCE_ADDRESS
# options / (list inference APIs)
# 

# TORCHSERVE_METRICS_ADDRESS
# TBD: get /metrics?...


def create_machinelearningmodel(self, request, *argv, **argd):
    form = self.get_form_class()(request.POST, request.FILES)
    form.is_valid()
    obj = form.save()
    task = load_model.delay(
        obj.id,
    )
    return (form, obj)


def get_output(self, request, *argv, **argd):
    user_text = request.POST["interaction"]
    if user_text.strip() == "":
        model_text = ""
    else:
        obj = self.get_object()
        model_text = requests.post(
            "{}/v2/models/{}/infer".format(settings.TORCHSERVE_INFERENCE_ADDRESS, obj.name),
            files={"data" : user_text}
        ).content
    return HttpResponse(model_text.decode("utf-8"))


app_name = "machine_learning"

urlpatterns = [
    path(
        '',
        AccordionView.as_view(
            preamble="""
            Roughly speaking, machine learning models are trained to perform a task when given input of some form.  In some cases, the input/output to/from a model follows a pattern simple enough to generate an interface for dynamically "conversing" with the model.
            """,
            children={
                "model" : MachineLearningModel,
                "url" : "machine_learning:machinelearningmodel_detail",
                "create_url" : "machine_learning:machinelearningmodel_create"
            }
        ),
        name="index"
    ),
    path(
        'machinelearningmodel/create/',
        BaseView.as_view(
            preamble="""
            Preparing a hosted model is an involved process, even without the complexities of training, but at a high level, this interface accepts .mar files as used in the TorchServe project.
            """,            
            model=MachineLearningModel,
            can_create=True,
            fields=["name", "url"],
            create_lambda=create_machinelearningmodel,
            initial={
                "url" : "http://localhost:8080/static/cdh/bloom350.mar",
                "name" : "bloom"
            }
        ),
        name="machinelearningmodel_create"
    ),
    path(
        'machinelearningmodel/<int:pk>/',
        BaseView.as_view(
            model=MachineLearningModel,
            update_lambda=get_output,
            can_delete=True,
            can_update=True,
            extra_fields={
                "interaction" : (CharField, {"widget" : MonacoEditorWidget(language="torchserve_text")}),
            }
        ),
        name="machinelearningmodel_detail"
    ),

]
