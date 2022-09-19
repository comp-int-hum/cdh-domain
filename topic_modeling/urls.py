import os
import os.path
from django.core.exceptions import ValidationError
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from django.views.decorators.cache import cache_page
from django.forms import FileField, modelform_factory, CharField
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.views.generic import DetailView, TemplateView
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm
from cdh.models import User
#from cdh.views import TabsView, AccordionView, VegaView, AtomicView, SelectView, generate_default_urls
#from cdh.widgets import MonacoEditorWidget
from .models import Lexicon, TopicModel
#from .models import Collection, Document, Lexicon, LabeledDocument, LabeledCollection, TopicModel
from .vega import WordCloud, SpatialDistribution, TemporalEvolution
from .tasks import extract_documents, train_model, apply_model
from .serializers import LexiconSerializer, TopicModelSerializer


#from .forms import LexiconForm, TopicDocumentTableForm
#from .views import WordTableView, LabeledDocumentView, DocumentTableView


# def create_topicmodel(self, request, *argv, **argd):
#     form = self.get_form_class()(request.POST, request.FILES)
#     if form.is_valid():
#         obj = form.save(commit=False)
#         obj.created_by = request.user
#         obj.save()
#         train_model.delay(obj.id)
#     else:
#         obj = None
#     return (form, obj)


# def create_collection(self, request, *argv, **argd):
#     form = self.get_form_class()(request.POST, request.FILES)
#     if form.is_valid():
#         if "file" in request.FILES:            
#             ufname = request.FILES["file"].name
#             path = settings.MEDIA_ROOT / "shared" / "topic_modeling" / "collections"
#             if not os.path.exists(path):
#                 os.makedirs(path)
#             obj = Collection.objects.create(
#                 name=form.cleaned_data["name"],
#             )
#             ofname = path / "{}_{}".format(obj.id, ufname)
#             with open(ofname, "wb") as ofd:
#                 for chunk in request.FILES["file"].chunks():
#                     ofd.write(chunk)
#             extract_documents.delay(
#                 obj.id,
#                 str(ofname),
#                 **request.POST
#             )
#         else:
#             obj = form.save(commit=False)
#             obj.created_by = request.user
#             obj.state = obj.COMPLETE
#             obj.save()
#     else:
#         obj = None
#     return (form, obj)


# def create_labeledcollection(self, request, *argv, **argd):
#     form = self.get_form_class()(request.POST, request.FILES)
#     if form.is_valid():
#         obj = form.save(commit=False)
#         obj.created_by = request.user
#         obj.save()
#         apply_model.delay(
#             obj.id,
#             request.user.id
#         )
#     else:
#         obj = None
#     return (form, obj)


app_name = "topic_modeling"
urlpatterns = [

    # Top-level interface
    path(
        '',
        TemplateView.as_view(
            template_name="cdh/accordion.html",
            extra_context={
                "items" : [
                    #Collection,
                    TopicModel,
                    Lexicon,
                    #LabeledCollection
                ]
            }
        ),
        name="index"
    ),
    # Special view for creating a Collection from zip/tar/json files (will be deprecated by RDF at some point)
    # path(
    #     'collection/create/',
    #     AtomicView.as_view(
    #         model=Collection,
    #         fields=["name", "query"],
    #         extra_fields={
    #             "file" : (FileField, {"required" : False}),
    #             "title_field" : CharField(initial="$.title"),
    #             "text_field" : CharField(initial="$.text"),
    #             "author_field" : CharField(initial="$.author"),
    #             "temporal_field" : CharField(initial="$.timestamp"),
    #             "spatial_field" : CharField(initial="$.geolocation"),
    #             "language_field" : CharField(initial="$.language"),
    #         },
    #         can_create=True,
    #         editable=True,
    #         create_lambda=create_collection,
    #     ),
    #     name="collection_create"
    # ),
    # Tabbed TopicModel view


    # path(
    #     'topicmodel/<int:pk>/',
    #     TabsView.as_view(
    #         model=TopicModel,
    #         tabs=[                
    #             {
    #                 "title" : "Word clouds",
    #                 "url" : "topic_modeling:topicmodel_wordcloud",
    #             },
    #             {
    #                 "title" : "Topic-word table",
    #                 "url" : "topic_modeling:topicmodel_wordtable",
    #             },
    #         ],
    #         can_delete=True
    #     ),
    #     name="topicmodel_detail"
    # ),
    # path(
    #     'topicmodel/create/',
    #     AtomicView.as_view(
    #         model=TopicModel,
    #         fields=["name", "collection", "topic_count"],
    #         can_create=True,
    #         create_lambda=create_topicmodel,
    #         initial={},
    #         editable=True
    #     ),
    #     name="topicmodel_create"
    # ),
    # path(
    #     'topicmodel/wordcloud/<int:pk>/',
    #     VegaView.as_view(
    #         model_attr="vega_words",
    #         model=TopicModel,
    #         vega_class=WordCloud,
    #     ),
    #     name="topicmodel_wordcloud"
    # ),
    # path(
    #     'topicmodel/wordtable/<int:pk>/',
    #     WordTableView.as_view(
    #         model=TopicModel
    #     ),
    #     name="topicmodel_wordtable"
    # ),
    
    # # LabeledCollection-related
    # path(
    #     'labeledcollection/<int:pk>/',
    #     TabsView.as_view(
    #         can_delete=True,
    #         model=LabeledCollection,
    #         tabs=[
    #             {
    #                 "title" : "Temporal",
    #                 "url" : "topic_modeling:labeledcollection_temporal"
    #             },
    #             {
    #                 "title" : "Spatial",
    #                 "url" : "topic_modeling:labeledcollection_spatial"
    #             },
    #             #{
    #             #    "title" : "Topic-document table",
    #             #    "url" : "topic_modeling:labeledcollection_topicdocumenttable",
    #             #},                
    #             {
    #                 "title" : "Highlighted Documents",
    #                 "url" : "topic_modeling:labeledcollection_labeleddocument_list",
    #             }
    #         ]
    #     ),
    #     name="labeledcollection_detail"
    # ),
    # path(
    #     'labeledcollection/temporal/<int:pk>/',
    #     VegaView.as_view(
    #         model_attr="vega_temporal",
    #         model=LabeledCollection,
    #         vega_class=TemporalEvolution,
    #     ),
    #     name="labeledcollection_temporal"
    # ),
    # path(
    #     'labeledcollection/spatial/<int:pk>/',
    #     VegaView.as_view(

    #         #<select id="{prefix}_topic" class="w-100"></select>
    #         model_attr="vega_spatial",
    #         model=LabeledCollection,
    #         vega_class=SpatialDistribution
    #     ),
    #     name="labeledcollection_spatial"
    # ),
    # path(
    #     'labeledcollection/topicdocumenttable/<int:pk>/',
    #     AtomicView.as_view(
    #         model=LabeledCollection,
    #         form_class=TopicDocumentTableForm,
    #     ),
    #     name="labeledcollection_topicdocumenttable"
    # ),    
    # path(
    #     'labeledcollection/create/',
    #     AtomicView.as_view(
    #         model=LabeledCollection,
    #         fields=["name", "collection", "model", "lexicon"],
    #         can_create=True,
    #         editable=True,
    #         create_lambda=create_labeledcollection,
    #     ),
    #     name="labeledcollection_create"
    # ),

    # # LabeledDocument-related
    # path(
    #     'labeleddocument/list/<int:pk>/',
    #     SelectView.as_view(
    #         model=LabeledCollection,
    #         related_model=LabeledDocument,
    #         relationship="labeledcollection",
    #         related_url="topic_modeling:labeleddocument_detail"
    #     ),
    #     name="labeledcollection_labeleddocument_list"
    # ),
    # path(
    #     'labeleddocument/<int:pk>/',
    #     LabeledDocumentView.as_view(),
    #     name="labeleddocument_detail"
    # ),    
]
#+ generate_default_urls(
#    TopicModel,
#    Lexicon,
#    Document,
#    LabeledDocument,
#    Collection,
#    LabeledCollection
#)
