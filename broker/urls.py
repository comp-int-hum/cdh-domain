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
from . import views
from cdh.views import CdhView, AccordionView
from cdh.widgets import MonacoEditorWidget
from .models import MachineLearningModel
from .widgets import MachineLearningModelInteractionWidget
from django.shortcuts import render
import requests
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

#def create_machinelearningmodel(self, request, *argv, **argd):
#    form = self.get_form_class()(request.POST, request.FILES)
#    form.is_valid()
#    obj = form.save()
#    print(request.POST, obj)
#    #train_model.delay(obj.id)
#    return (obj, HttpResponseRedirect(obj.get_absolute_url()))

def get_output(self, request, *argv, **argd):
    user_text = request.POST["interaction"]
    if user_text.strip() == "":
        model_text = ""
    else:
        obj = self.get_object()
        print(user_text)
        print("{}/v2/models/{}/infer".format(settings.TORCHSERVE_INFERENCE_ADDRESS, obj.name))
        model_text = requests.post(
            "{}/v2/models/{}/infer".format(settings.TORCHSERVE_INFERENCE_ADDRESS, obj.name),
            files={"data" : user_text}
        ).content
    return HttpResponse(model_text.decode("utf-8"))
    #return render(request, "cdh/simple_interface.html", {"content" : model_text.decode("utf-8")})

app_name = "broker"

urlpatterns = [
    path(
        '',
        AccordionView.as_view(
            children={
                "model" : MachineLearningModel,
                "url" : "broker:machinelearningmodel_detail",
                "create_url" : "broker:machinelearningmodel_create"
            }
        ),
        name="index"
    ),
    path(
        'machinelearningmodel/create/',
        CdhView.as_view(
            model=MachineLearningModel,
            can_create=True,
            fields=["name", "url"],
            initial={
                "url" : "http://localhost:8080/static/cdh/bloom350.mar",
                "name" : "bloom"
            }
        ),
        name="machinelearningmodel_create"
    ),
    path(
        'machinelearningmodel/<int:pk>/',
        CdhView.as_view(
            preamble="""This model is similar to, but approximately 1/1000th the size of, the GPT-3 language model and similar.  Enter text below, then press "Shift-Tab" for the model to generate the next token.""",
            model=MachineLearningModel,
            update_lambda=get_output,
            extra_fields={
                "interaction" : (CharField, {"widget" : MachineLearningModelInteractionWidget})
            }
        ),
        name="machinelearningmodel_detail"
    ),

]
