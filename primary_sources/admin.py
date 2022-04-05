from django.contrib import admin
from .models import Dataset
from .forms import DatasetForm
import rdflib
import logging
from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import assign_perm
from cdh import settings, admin as cdhadmin
import requests


class DatasetAdmin(GuardedModelAdmin):
    form = DatasetForm

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
        graphs = {}
        for graph_name in ["schema", "annotation", "data"]:
            fid = request.FILES.get("{}_file".format(graph_name), None)
            graphs[graph_name] = rdflib.Graph()
            if fid:
                graphs[graph_name].parse(data=fid.read(), format=fid.content_type)
        if settings.USE_JENA:
            super().save_model(request, obj, form, change)
            for graph_name, graph in graphs.items():
                requests.post(
                    "http://{}:{}/$/datasets".format(settings.JENA_HOST, settings.JENA_PORT),
                    params={"dbName" : "{}_{}".format(obj.id, graph_name), "dbType" : "tdb"},
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
