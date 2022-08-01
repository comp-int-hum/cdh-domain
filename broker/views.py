from django.shortcuts import render
from django.http import HttpResponse
from cdh.views import CdhView
from .models import MachineLearningModel
from cdh.widgets import VegaWidget, MonacoEditorWidget
import requests

#res = requests.post("http://localhost:8080/predictions/squeezenet1_1", files={'data': open('docs/images/dogs-before.jpg', 'rb'), 'data': open('docs/images/kitten_small.jpg', 'rb')})

