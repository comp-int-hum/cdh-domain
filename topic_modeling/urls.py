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
from django.views.generic import DetailView
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm
from cdh.models import User
from cdh.views import TabsView, AccordionView, VegaView, BaseView, SelectView
from cdh.widgets import MonacoEditorWidget
from .models import Collection, Document, Lexicon, LabeledDocument, LabeledCollection, TopicModel
from .vega import WordCloud, SpatialDistribution, TemporalEvolution
from .tasks import extract_documents, train_model, apply_model
from .forms import LexiconForm, TopicDocumentTableForm
from .views import WordTableView, LabeledDocumentView, DocumentTableView


def create_topicmodel(self, request, *argv, **argd):
    form = self.get_form_class()(request.POST, request.FILES)
    if form.is_valid():
        obj = form.save()
        train_model.delay(obj.id)
    else:
        obj = None
    return (form, obj)


def create_collection(self, request, *argv, **argd):
    form = self.get_form_class()(request.POST, request.FILES)
    if form.is_valid():
        ufname = request.FILES["file"].name
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
    else:
        obj = None
    return (form, obj)


def create_labeledcollection(self, request, *argv, **argd):
    form = self.get_form_class()(request.POST, request.FILES)
    if form.is_valid():
        obj = form.save()
        apply_model.delay(
            obj.id,
        )
    else:
        obj = None
    return (form, obj)


app_name = "topic_modeling"
urlpatterns = [

    # Top-level interface
    path(
        '',
        AccordionView.as_view(
            preamble="""
            Topic models and manual lexicons are two methods for exploring how text collections differ across dimensions like author, space, and time.  This interface allows scholars to upload collections of documents, train topic models on them and define lexicons, and apply both models and lexicons to the collections to produce labeled collections that surface semantically-coherent information.
            """,
            children=[
                {
                    "title" : "Collections",
                    "url" : "topic_modeling:collection_list"
                },
                {
                    "title" : "Topic Models",
                    "url" : "topic_modeling:topicmodel_list"
                },
                {
                    "title" : "Lexicons",
                    "url" : "topic_modeling:lexicon_list"
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
        BaseView.as_view(
            model=Collection,
            fields=["name"],
            can_delete=True
        ),
        name="collection_detail"
    ),
    path(
        'collection/create/',
        BaseView.as_view(
            preamble="""
            Collections can be created from several data formats coupled with a simple description of how to map its fields.  At a minimum, a text field must be specified.  Optionally, temporal, spatial, language, and authorial fields can also be specified.  The mapping uses <a href="https://goessner.net/articles/JsonPath/">JsonPath</a> syntax to be maximally expressive for that common format, but as can be seen in the default values below, this is usually as simple as writing "$.FIELD_NAME".
            
            The currently recognized formats are as follows:
            
            <dl>
              <dt>CSV file ending in "csv" or "csv.gz"</dt>
              <dd>Should have an initial header row with the column names, and the field mapping is trivial: "$.text" corresponds to the column "text".</dd>
              <dt>JSON file ending in "json" or "json.gz"</dt>
              <dd>Should contain either a top-level JSON list of objects (i.e. the file begins with '[' and ends with ']'), or have one JSON object per line (i.e. the file begins with '{' and ends with '}').  The field mapping follows the semantics of JsonPath linked above.</dd>
              <dt>Zip file ending in ".zip", or Tar file ending in "tar" or "tar.gz"</dt>
              <dd>These file formats are "archives", meaning they contain other files.  In either case, each contained file should have a name ending in ".txt" and contain the text of a single document.  The one exception is an optional file ending in ".csv", a CSV file with an initial header row, a column "file_name" containing names of ".txt" files in the archive, and any number of additional columns that will be interpreted the same way as the CSV format described above.</dd>
            </dl>
            To train a model you will want to have a substantial amount of text, at least hundreds of pages.  If the collection will simply have an existing model or lexicon applied to it, the quantity does not matter.
            """,
            model=Collection,
            fields=["name"],
            extra_fields={
                "file" : (FileField, {"required" : True}),
                "title_field" : CharField,
                "text_field" : CharField,                
                "author_field" : CharField,
                "temporal_field" : CharField,
                "spatial_field" : CharField,
                "language_field" : CharField,
            },
            initial={
                "title_field" : "$.title",
                "text_field" : "$.text",
                "author_field" : "$.author",
                "temporal_field" : "$.timestamp",
                "spatial_field" : "$.geolocation",
                "language_field" : "$.language",
            },
            can_create=True,
            create_lambda=create_collection,
        ),
        name="collection_create"
    ),

    # Lexicon-related
    path(
        'lexicon/<int:pk>/',
        BaseView.as_view(
            model=Lexicon,
            form_class=LexiconForm,
            can_update=True,
            can_delete=True
        ),
        name="lexicon_detail"
    ),
    path(
        'lexicon/create/',
        BaseView.as_view(
            preamble="""
            A lexicon is simply specified as a mapping from meaningful labels (could be topics, sentiments, styles,
            etc) to lists of word-patterns that indicate the label.  The syntax should be clear from the initial example in
            the editor below.  The word-patterns can include "wildcards" such as in "sad.*", which will match "sad", "sadly",
            "saddened", etc.  Note that it is a period followed by an asterisk, not just an asterisk (this is because
            you can actually specify arbitrary "regular expressions" as defined in the Python language's core library,
            for advanced situations).  Bear in mind that, while the word-patterns are applied to each word of the documents,
            and therefore you needn't worry about wildcards matching across multiple words, you should still be careful in
            using them: they can easily become too general and match many unintended words.  Also, the collective matching
            behavior of the different labels should not overlap: if two labels both have word-patterns matching a word, the
            word will only "count" for one of them, chosen at random.
            """,
            model=Lexicon,
            #form_class=LexiconForm,
            fields=["name", "lexical_sets"],
            can_create=True,
            widgets = {
                'lexical_sets': MonacoEditorWidget(language="json", content_field="lexical_sets")
            }
        ),
        name="lexicon_create"
    ),

    # TopicModel-related
    path(
        'topicmodel/<int:pk>/',
        TabsView.as_view(
            model=TopicModel,
            tabs=[                
                {
                    "title" : "Word clouds",
                    "url" : "topic_modeling:topicmodel_wordcloud",
                },
                {
                    "title" : "Topic-word table",
                    "url" : "topic_modeling:topicmodel_wordtable",
                },
            ],
            can_delete=True
        ),
        name="topicmodel_detail"
    ),
    path(
        'topicmodel/create/',
        BaseView.as_view(
            model=TopicModel,
            fields=["name", "collection", "topic_count", "lowercase", "max_context_size", "maximum_documents", "passes"],
            can_create=True,
            create_lambda=create_topicmodel,
            initial={},
            preamble="""
            The most important choices in training a topic model are the collection it will be based on, and
            the number of topics to infer.
            """
        ),
        name="topicmodel_create"
    ),
    path(
        'topicmodel/wordcloud/<int:pk>/',
        VegaView.as_view(
            model_attr="vega_words",
            model=TopicModel,
            vega_class=WordCloud,
            preamble="""
            Each word cloud corresponds to a topic inferred by the model, with the words sized according to their
            likelihood.  Note that the spatial arrangement is not meaningful in such visualizations.
            """
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
        TabsView.as_view(
            can_delete=True,
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
                #    "title" : "Topic-document table",
                #    "url" : "topic_modeling:labeledcollection_topicdocumenttable",
                #},                
                {
                    "title" : "Highlighted Documents",
                    "url" : "topic_modeling:labeledcollection_labeleddocument_list",
                }
            ]
        ),
        name="labeledcollection_detail"
    ),
    path(
        'labeledcollection/temporal/<int:pk>/',
        VegaView.as_view(
            model_attr="vega_temporal",
            model=LabeledCollection,
            vega_class=TemporalEvolution,
            preamble="""
            If the original collection included temporal information, this figure shows the waxing and waning of the inferred topics over time.  As the mouse moves over the figure, the display shows the top words for the highlighted topic, and the date at which the pointer is located.
            <input id="{prefix}_topicinfo" class="w-100"></input>
            <input id="{prefix}_timeinfo" class="w-100"></input>
            """
        ),
        name="labeledcollection_temporal"
    ),
    path(
        'labeledcollection/spatial/<int:pk>/',
        VegaView.as_view(
            preamble="""
            If the original collection included spatial information, this figure shows a rudimentary projection onto a world map.  Hovering over points will show the text of the particular document.
            """,
            #<select id="{prefix}_topic" class="w-100"></select>
            model_attr="vega_spatial",
            model=LabeledCollection,
            vega_class=SpatialDistribution
        ),
        name="labeledcollection_spatial"
    ),
    path(
        'labeledcollection/topicdocumenttable/<int:pk>/',
        BaseView.as_view(
            model=LabeledCollection,
            form_class=TopicDocumentTableForm,
        ),
        name="labeledcollection_topicdocumenttable"
    ),    
    path(
        'labeledcollection/create/',
        BaseView.as_view(
            model=LabeledCollection,
            fields=["name", "collection", "model", "lexicon", "maximum_documents"],
            can_create=True,
            create_lambda=create_labeledcollection,
            preamble="""
            To create a labeled collection, choose a meaningful name, and then select the collection to be labeled, and either a topic model or a lexicon to use.  After creation, it will take a while for the process to complete: until then, the new entry will display a progress indicator, or a red error message if something goes wrong.
            """
        ),
        name="labeledcollection_create"
    ),

    # LabeledDocument-related
    path(
        'labeleddocument/list/<int:pk>/',
        SelectView.as_view(
            preamble="""
            This dropdown box lets you select specific documents from the collection and inspect how the words were annotated by topic.  At the moment this simply highlights, when the pointer passes over a word with a particular topic, the other words from the same topic.
            """,
            model=LabeledCollection,
            related_model=LabeledDocument,
            relationship="labeledcollection",
            related_url="topic_modeling:labeleddocument_detail"
        ),
        name="labeledcollection_labeleddocument_list"
    ),
    path(
        'labeleddocument/<int:pk>/',
        LabeledDocumentView.as_view(),
        name="labeleddocument_detail"
    ),    
] + [
        path(
            '{}/list/'.format(model._meta.model_name),
            AccordionView.as_view(
                model=model,
                preamble=preamble,
                children={
                    "model" : model,
                    "url" : "topic_modeling:{}_detail".format(model._meta.model_name),
                    "create_url" : "topic_modeling:{}_create".format(model._meta.model_name),
                },
            ),
            name="{}_list".format(model._meta.model_name)
        ) for model, preamble in [
            (TopicModel, """
            A topic model is a learned representation that tries to explain observed patterns of word-occurrence (i.e. documents) by positing some number of unobserved "topics", each of which consists of a different distribution over the vocabulary.
            """),
            (Lexicon, """
            In a lexicon, the scholar specifies topics directly as lists of word(-patterns), using domain knowledge of the relevant semantics to combine various ways of evincing the same phenomena of interest.
            """),
            (Collection, """
            A collection is a set of text documents with optional additional information about author, location, time, and other arbitrary properties that the scholar deems interesting.
            """),
            (LabeledCollection, """
            A labeled collection is the result of applying either a lexicon or a topic model to a collection.  In either case, each word in each document is potentially assigned a topic.  This information is aggregated and displayed in several automatic ways: if the original collection had temporal or spatial fields, for instance.  A document-level view allows the scholar to directly inspect how words in specific documents have been labeled.
            """)
        ]
]
