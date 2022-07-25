from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from django.views.generic.list import ListView
from django.views.generic.edit import FormView, CreateView, UpdateView
from cdh.views import AccordionView, TabView
from django.http import HttpResponse, HttpResponseRedirect
from cdh.views import TabView, AccordionView, VegaView, CdhView, CdhSelectView
from django.forms import FileField, modelform_factory, CharField
from .models import PrimarySource
from .vega import PrimarySourceSchemaGraph
from .forms import PrimarySourceEditorForm


def create_primarysource(self, request, *argv, **argd):
    form = self.get_form_class()(request.POST, request.FILES)
    form.is_valid()
    obj = form.save(commit=False)
    obj.save(
        schema_fd=request.FILES.get("schema_file", None),
        data_fd=request.FILES.get("data_file", None),
        annotation_fd=request.FILES.get("annotation_file", None),
        materials_fd=request.FILES.get("materials_file", None),
    )
    return (obj, HttpResponseRedirect(obj.get_absolute_url()))


app_name = "primary_sources"
urlpatterns = [
    path(
        '',
        AccordionView.as_view(
            model=PrimarySource,
            preamble="""
            Primary sources, their domain-specific structure, and the scholarly knowledge and
            formalisms associated with them, are the cornerstone of empirical humanistic inquiry.
            """,
            children={
                "model" : PrimarySource,
                "url" : "primary_sources:primarysource_detail",
                "create_url": "primary_sources:primarysource_create"
            }
        ),
        name="index"
    ),
    path(
        'primarysource/create/',
        CdhView.as_view(
            preamble="""
            A primary source can be created by specifying a meaningful name and (optionally) files
            containing a domain schema, data, and annotations.  These must all be in RDF .ttl format.
            A fourth file can be a zip archive containing items too large to directly include in the
            graph representations (TBD).
            """,
            model=PrimarySource,
            fields=["name"],
            extra_fields={
                "schema_file" : (
                    FileField,
                    {
                        "required" : False,
                    }
                ),
                "data_file" : (
                    FileField,
                    {
                        "required" : False,
                    }
                ),
                "annotation_file" : (
                    FileField,
                    {
                        "required" : False,
                    }
                ),
                "materials_file" : (
                    FileField,
                    {
                        "required" : False,
                    }
                ),
            },
            can_create=True,
            create_lambda=create_primarysource,
        ),
        name="primarysource_create"
    ),
    path(
        'primarysource/<int:pk>/',
        TabView.as_view(
            model=PrimarySource,
            tabs=[
                {
                    "title" : "Graphical",
                    "url" : "primary_sources:primarysource_graphical"
                },
                {
                    "title" : "Editor",
                    "url" : "primary_sources:primarysource_editor"
                }
            ]
        ),
        name="primarysource_detail"
    ),
    path(
        'primarysource/editor/<int:pk>/',
        CdhView.as_view(
            model=PrimarySource,
            form_class=PrimarySourceEditorForm,            
        ),
        name="primarysource_editor"
    ),
    path(
        'primarysource/graphical/<int:pk>/',
        VegaView.as_view(
            model_attr="vega_triples",
            model=PrimarySource,
            vega_class=PrimarySourceSchemaGraph,
        ),
        name="primarysource_graphical"
    ),
    
    # add Query interface here
]
