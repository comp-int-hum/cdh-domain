from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from cdh import settings
from . import models
from . import forms
import requests
import rdflib
from rdflib.tools.rdf2dot import rdf2dot
import io
import graphviz

@login_required(login_url="/accounts/login/")
def index(request):
    context = {
    }
    return render(request, "primary_sources/index.html", context)

@login_required(login_url="/accounts/login/")
def dataset_list(request):
    if request.method == "POST":
        f = forms.AddDatasetForm(request.POST, request.FILES)
        if f.is_valid():
            f.save()
    
    context = {
        "datasets" : models.Dataset.objects.all(),
        "form" : forms.AddDatasetForm(),
    }
    return render(request, "primary_sources/dataset_list.html", context)

@login_required(login_url="/accounts/login/")
def dataset_detail(request, did):
    context = {
        "dataset" : models.Dataset.objects.get(id=did) 
    }
    resp = requests.get(
        "http://{}:{}/{}_{}/data".format(settings.JENA_HOST, settings.JENA_PORT, did, "schema"),
        headers={"Accept" : "application/ld+json"},
        auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
    )
    #g = rdflib.Graph()
    #g.parse(resp.content, format="application/ld+json")
    #ss = io.StringIO()
    #rdf2dot(g, ss)
    #dot = ss.getvalue()
    #graphviz.Digraph(body=
    return render(request, "primary_sources/dataset_detail.html", context)
