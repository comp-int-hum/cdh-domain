import json
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
import json
from cdh import settings
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from primary_sources.models import Dataset
import requests
#from .dataset_schema_graph import DatasetSchemaGraph
#from .dataset_ontology_tree import DatasetOntologyTree
from .dataset_ontology_graph import DatasetOntologyGraph
#import graphviz

def webvowl(request):
    context = {
    }
    return render(request, "primary_sources/webvowl.html", context)

#@login_required(login_url="/accounts/login/")
def index(request):
    context = {
    }
    return render(request, "primary_sources/index.html", context)

#@login_required(login_url="/accounts/login/")
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

#@login_required(login_url="/accounts/login/")
def dataset_detail(request, did):
    context = {
        "dataset" : models.Dataset.objects.get(id=did) 
    }
    #resp = requests.get(
    #    "http://{}:{}/{}_{}/data".format(settings.JENA_HOST, settings.JENA_PORT, did, "schema"),
    #    headers={"Accept" : "application/ld+json"},
    #    auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
    #)
    # class_query = """
    # PREFIX owl: <http://www.w3.org/2002/07/owl#>
    # PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    # PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    # SELECT DISTINCT ?t ?u ?v ?l
    # WHERE {
    #     ?t rdf:type owl:Class .        
    # }
    # """
    relationship_query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>    
    SELECT DISTINCT ?parent ?child
    WHERE {
        ?child rdfs:subClassOf+ ?parent .
        FILTER (!isBlank(?parent))
    }
    """
    # resp = requests.get(
    #    "http://{}:{}/{}_{}/query".format(settings.JENA_HOST, settings.JENA_PORT, did, "schema"),
    #    #headers={"Accept" : "text/turtle"},
    #    params={"query" : class_query},
    #    auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
    # )
    # out = json.loads(resp.content.decode("utf-8"))
    hierarchy = {}
    # for c in out["results"]["bindings"]:
    #     hierarchy[c["t"]["value"]] = set()
    resp = requests.get(
       "http://{}:{}/{}_{}/query".format(settings.JENA_HOST, settings.JENA_PORT, did, "schema"),
       #headers={"Accept" : "text/turtle"},
       params={"query" : relationship_query},
       auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
    )
    print(resp.content.decode("utf-8"))
    j = json.loads(resp.content.decode("utf-8"))
    print(j)
    for row in j["results"]["bindings"]:
        child = row["child"]["value"]
        parent = row["parent"]["value"]
        hierarchy[child] = hierarchy.get(child, []) + [parent]
    context["hierarchy"] = {k.split("#")[-1] : [c.split("#")[-1] for c in v] for k, v in hierarchy.items() if "#" in k}

    return render(request, "primary_sources/dataset_detail.html", context)


def dataset_ontology_graph(request, dataset_id):
    relationship_query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>    
    SELECT DISTINCT ?parent ?child
    WHERE {
        ?child rdfs:subClassOf+ ?parent .
        FILTER (!isBlank(?parent))
    }
    """
    hierarchy = {}
    resp = requests.get(
       "http://{}:{}/{}_{}/query".format(settings.JENA_HOST, settings.JENA_PORT, dataset_id, "schema"),
       params={"query" : relationship_query},
       auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
    )
    j = json.loads(resp.content.decode("utf-8"))
    for row in j["results"]["bindings"]:
        child = row["child"]["value"]
        parent = row["parent"]["value"]
        hierarchy[child] = hierarchy.get(child, []) + [parent]
    retval = DatasetOntologyGraph(hierarchy).json
    return JsonResponse(retval)


