from django.contrib import admin
from .models import Dataset
from .forms import DatasetForm
import rdflib
import json
import logging
from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import assign_perm
from cdh import settings, admin as cdhadmin
import requests


class DatasetAdmin(GuardedModelAdmin):
    form = DatasetForm
    actions = ["generate_schema"]

    @admin.action(description="Generate schema from data")
    def generate_schema(self, request, queryset):
        query = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <https://schema.org/>
PREFIX : <http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine#>
SELECT DISTINCT ?st ?r ?ot datatype(?o)
WHERE {
  ?s rdf:type ?st .
  ?s ?r ?o .
  OPTIONAL { ?o rdf:type ?ot }
}
        """
        for obj in queryset:
            resp = requests.get(
                "http://{}:{}/{}_{}/query".format(settings.JENA_HOST, settings.JENA_PORT, obj.id, "data"),
                #headers={"Accept" : "text/turtle"},
                params={"query" : query},
                auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
            )
            j = json.loads(resp.content.decode("utf-8"))
            for row in j["results"]["bindings"]:
                print(row)
    
    def has_module_permission(self, request):
        return request.user.is_authenticated    

    def has_add_permission(self, request):
        return request.user.is_authenticated

    def has_view_permission(self, request, obj=None):
        return request.user.is_authenticated and (obj==None or (request.user.has_perm("view_dataset", obj)))

    def has_change_permission(self, request, obj=None):
        return obj == None or (request.user.is_authenticated and (request.user.has_perm("change_dataset", obj)))

    def has_delete_permission(self, request, obj=None):
        return obj == None or (request.user.is_authenticated and (request.user.has_perm("delete_dataset", obj)))
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        for graph_name in ["schema", "annotation", "data"]:
            fid = request.FILES.get("{}_file".format(graph_name), None)
            if settings.USE_JENA:
                dbName = "{}_{}".format(obj.id, graph_name)
                requests.post(
                    "http://{}:{}/$/datasets".format(settings.JENA_HOST, settings.JENA_PORT),
                    params={"dbName" : dbName, "dbType" : "tdb"},
                    auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
                )
                if fid:
                    requests.put(
                        "http://{}:{}/{}/data".format(settings.JENA_HOST, settings.JENA_PORT, dbName),
                        headers={"default" : "", "Content-Type" : fid.content_type},
                        data=fid,
                        auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)                    
                    )
        
        if request.user.is_authenticated:
            assign_perm("view_dataset", request.user, obj)
            assign_perm("change_dataset", request.user, obj)
            assign_perm("delete_dataset", request.user, obj)            
    
    def delete_model(self, request, obj):
        for graph_name in ["schema", "annotation", "data"]:
            if settings.USE_JENA:
                requests.delete(
                    "http://{}:{}/$/datasets/{}_{}".format(settings.JENA_HOST, settings.JENA_PORT, obj.id, graph_name),
                    auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)                    
                )
        super().delete_model(request, obj)

        
    def delete_queryset(self, request, queryset):
        for obj in queryset:
            for graph_name in ["schema", "annotation", "data"]:
                if settings.USE_JENA:
                    requests.delete(
                        "http://{}:{}/$/datasets/{}_{}".format(settings.JENA_HOST, settings.JENA_PORT, obj.id, graph_name),
                        auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)                    
                    )
        super().delete_queryset(request, queryset)

        
cdhadmin.site.register(Dataset, DatasetAdmin)
