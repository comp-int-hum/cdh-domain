import os
import os.path
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from django.views.decorators.cache import cache_page
from django.forms import FileField, modelform_factory, CharField
from django.http import HttpResponse, HttpResponseRedirect
from . import views
from . import models
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.views.generic import DetailView
from .models import Collection, Document, Lexicon, LabeledDocument, LabeledCollection, TopicModel
from .forms import LexiconForm, CollectionCreateForm, TopicModelForm, TopicModelWordCloudForm, TopicModelWordTableForm
from .views import WordTableView, CollectionCreateView
from cdh.views import TabView, AccordionView, VegaView, CdhView
from .vega import TopicModelWordCloud, SpatialDistribution, TemporalEvolution
from .tasks import extract_documents, train_model, apply_model


def create_topicmodel(self, request, *argv, **argd):
    form = self.get_form_class()(request.POST, request.FILES)
    form.is_valid()
    obj = form.save()
    train_model.delay(obj.id)
    return HttpResponseRedirect(obj.get_absolute_url())


def create_collection(self, request, *argv, **argd):
    form = self.get_form_class()(request.POST, request.FILES)
    form.is_valid()
    ufname = request.FILES["file"].name
    #ext = os.path.splitext(ufname)[-1]
    path = settings.MEDIA_ROOT / "shared" / "topic_modeling" / "collections"
    if not os.path.exists(path):
        os.makedirs(path)
    obj = Collection.objects.create(
        name=form.cleaned_data["name"],
    )        
    ofname = path / "{}_{}".format(obj.id, ufname)
    with open(ofname, "wb") as ofd:
        for chunk in request.FILES["file"].chunks():
            ofd.write(chunk)
    extract_documents.delay(
        obj.id,
        str(ofname),
        **request.POST
    )
    return HttpResponseRedirect(obj.get_absolute_url())


app_name = "topic_modeling"
urlpatterns = [

    # Top-level interface
    path(
        '',
        AccordionView.as_view(
            model=TopicModel,
            children=[
                {
                    "title" : "Models",
                    "url" : "topic_modeling:topicmodel_list"
                },
                {
                    "title" : "Lexicons",
                    "url" : "topic_modeling:lexicon_list"
                },
                {
                    "title" : "Collections",
                    "url" : "topic_modeling:collection_list"
                },
                {
                    "title" : "Labeled Collections",
                    "url" : "topic_modeling:labeledcollection_list"
                }                                
            ]
        ),
        name="index"
    ),

    # Collection-related
    path(
        'collection/<int:pk>/',
        CdhView.as_view(
            model=Collection,
            fields=["name"],
            can_delete=True
        ),
        name="collection_detail"
    ),
    path(
        'collection/create/',
        CdhView.as_view(
            model=Collection,
            fields=["name"],
            extra_fields={
                "file" : FileField,
                "title_field" : CharField,
                "text_field" : CharField,                
                "author_field" : CharField,
                "temporal_field" : CharField,
                "spatial_field" : CharField                
            },
            initial={
                "title_field" : "$.id_str",
                "text_field" : "$.text",
                "author_field" : "$.user.screen_name",
                "temporal_field" : "$.created_at",
                "spatial_field" : "$.user.location"
            },
            can_create=True,
            create_lambda=create_collection,
        ),
        name="collection_create"
    ),

    # Lexicon-related
    path(
        'lexicon/<int:pk>/',
        CdhView.as_view(
            model=Lexicon,
            form_class=LexiconForm,
            can_update=True,
            can_delete=True
        ),
        name="lexicon_detail"
    ),
    path(
        'lexicon/create/',
        CdhView.as_view(
            model=Lexicon,
            form_class=LexiconForm,
            can_create=True
        ),
        name="lexicon_create"
    ),

    # TopicModel-related
    path(
        'topicmodel/detail/<int:pk>/',
        TabView.as_view(
            model=TopicModel,
            tabs=[                
                {
                    "title" : "Word clouds",
                    "url" : "topic_modeling:topicmodel_wordcloud"
                },
                {
                    "title" : "Topic table",
                    "url" : "topic_modeling:topicmodel_wordtable"
                }
            ],
            can_delete=True
        ),
        name="topicmodel_detail"
    ),
    path(
        'topicmodel/create/',
        CdhView.as_view(
            model=TopicModel,
            fields=["name", "collection", "topic_count", "lowercase", "max_context_size", "maximum_documents"],
            can_create=True,
            create_lambda=create_topicmodel,
            initial={}
        ),
        name="topicmodel_create"
    ),
    path(
        'topicmodel/wordcloud/<int:pk>/',
        VegaView.as_view(
            model_attr="vega_words",
            model=TopicModel,
            vega_class=TopicModelWordCloud
        ),
        name="topicmodel_wordcloud"
    ),
    path(
        'topicmodel/wordtable/<int:pk>/',
        WordTableView.as_view(
            model=TopicModel
        ),
        name="topicmodel_wordtable"
    ),
    
    # LabeledCollection-related
    path(
        'labeledcollection/detail/<int:pk>/',
        TabView.as_view(
            model=LabeledCollection,
            tabs=[
                {
                    "title" : "Temporal",
                    "url" : "topic_modeling:labeledcollection_temporal"
                },
                {
                    "title" : "Spatial",
                    "url" : "topic_modeling:labeledcollection_spatial"
                },
                #{
                #    "title" : "Highlighted Documents",
                #    "url" : "topic_modeling:labeleddocument_list",
                #}
            ]
        ),
        name="labeledcollection_detail"
    ),
    path(
        'labeledcollection/temporal/<int:pk>/',
        VegaView.as_view(
            model_attr="vega_temporal",
            model=LabeledCollection,
            vega_class=TemporalEvolution
        ),
        name="labeledcollection_temporal"
    ),
    path(
        'labeledcollection/spatial/<int:pk>/',
        VegaView.as_view(
            model_attr="vega_spatial",
            model=LabeledCollection,
            vega_class=SpatialDistribution
        ),
        name="labeledcollection_spatial"
    ),
    path(
        'labeledcollection/create/',
        CdhView.as_view(
            model=LabeledCollection,
            fields=["name", "collection", "model", "lexicon"],
            can_create=True
        ),
        name="labeledcollection_create"
    ),

    # LabeledDocument-related
    # path(
    #     'labeleddocument/<int:pk>/',
    #     UpdateView.as_view(model=LabeledDocument, fields=["name"], template_name="cdh/simple_form.html"),
    #     name="labeleddocument_update"
    # ),
    # path(
    #     'labeleddocument/create/',
    #     CreateView.as_view(model=LabeledDocument, fields=["name"], template_name="cdh/simple_form.html"),
    #     name="labeleddocument_create"
    # ),

] + [
        path(
            '{}/list/'.format(model._meta.model_name),
            AccordionView.as_view(
                model=model,
                children={
                    "model" : model,
                    "url" : "topic_modeling:{}_detail".format(model._meta.model_name),
                    "create_url" : "topic_modeling:{}_create".format(model._meta.model_name)
                }
            ),
            name="{}_list".format(model._meta.model_name)
        ) for model in [TopicModel, Lexicon, Collection, LabeledCollection]]
