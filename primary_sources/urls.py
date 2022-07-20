from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from django.views.generic.list import ListView
from django.views.generic.edit import FormView, CreateView, UpdateView
from cdh.views import AccordionView, TabView
from .models import PrimarySource
from .forms import PrimarySourceForm, PrimarySourceGraphicalForm, PrimarySourceEditorForm, QueryForm
from .views import primarysource_relational_graph_spec

# the overall accordion and tab layout for primary source management
spec = {
    "children" : [
        {
            "model_class" : PrimarySource,
            "tabs" : [
                {
                    "title" : "Graph",
                    "url" : "primary_sources:primarysource_graphical_update"
                },
                {
                    "title" : "Editor",
                    "url" : "primary_sources:primarysource_editor_update"
                },
                #{
                #    "title" : "Queries",
                #}
            ]
        },
    ],
}


app_name = "primary_sources"
urlpatterns = [
    #path(
    #    '',
    #    AccordionTabView.as_view(spec=spec),
    #    name="index"
    #),
    path(
        '',
        AccordionView.as_view(
            model=PrimarySource,
            children={
                "model" : PrimarySource,
                "url" : "primary_sources:primarysource_tabs"
            }
        ),
        name="index"
    ),
    path(
        'primarysource/tabs/<int:pk>/',
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
        name="primarysource_tabs"
    ),
    # path(
    #     'primarysource/<int:pk>/',
    #     UpdateView.as_view(model=PrimarySource, form_class=PrimarySourceForm, template_name="cdh/simple_form.html"),
    #     name="primarysource_update"
    # ),
    # path(
    #     'primarysource/create/',
    #     CreateView.as_view(model=PrimarySource, form_class=PrimarySourceForm, template_name="cdh/simple_form.html"),
    #     name="primarysource_create"
    # ),

    path(
        'primarysource/editor/<int:pk>/',
        UpdateView.as_view(model=PrimarySource, form_class=PrimarySourceEditorForm, template_name="cdh/simple_form.html"),
        name="primarysource_editor"
    ),
    path(
        'primarysource/graphical/<int:pk>/',
        UpdateView.as_view(model=PrimarySource, form_class=PrimarySourceGraphicalForm, template_name="cdh/simple_form.html"),
        name="primarysource_graphical"
    ),

    
    
    #path(
    #    'primarysource_relational_graph/<int:pk>/',
    #    UpdateView.as_view(model=Primarysource, form_class=PrimarysourceVegaForm, template_name="cdh/simple_form.html"),
    #    name="primarysource_relational_graph"
    #),
    #path('primarysource/relational_graph_spec/<int:pk>/', primarysource_relational_graph_spec, name="primarysource_relational_graph_spec"),
]
