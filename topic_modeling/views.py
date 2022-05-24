import pickle
import gzip
import json
from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView, TemplateView
from django.urls import reverse
from guardian.shortcuts import get_objects_for_user
from django.contrib.auth.decorators import login_required
from . import models
from . import forms
from . import tasks
from gensim.models import LdaModel
from gensim.corpora import Dictionary
from .wordcloud import WordCloud
from .models import TopicModel, LabeledCollection, Lexicon, Collection, LabeledDocument, Document
from django.http import JsonResponse
from topic_modeling import apps
# TODO: needs pagination, breadcrumbs

def index(request):
    context = {
        "breadcrumbs" : [("Topic modeling", None)],
    }
    return render(request, "topic_modeling/index.html", context)


def collection_list(request):
    context = {
        "collections" : [],
        "breadcrumbs" : [("Topic modeling", index)]
    }
    for collection in get_objects_for_user(request.user, "topic_modeling.view_collection"):
        context["collections"].append(
            (
                collection,
                get_objects_for_user(
                    request.user,
                    "topic_modeling.view_labeledcollection",
                    LabeledCollection.objects.filter(collection=collection)
                ),
                get_objects_for_user(
                    request.user,
                    "topic_modeling.view_topicmodel",
                    TopicModel.objects.filter(collection=collection)
                )
            )
        )
    return render(request, "topic_modeling/collection_list.html", context)


def topic_model_list(request):
    context = {
        "topic_models" : [],
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index")]
    }
    for topic_model in get_objects_for_user(request.user, "topic_modeling.view_topicmodel"):
        context["topic_models"].append(
            (
                topic_model,
                get_objects_for_user(
                    request.user,
                    "topic_modeling:view_labeledcollection",
                    klass=models.LabeledCollection.objects.filter(model=topic_model)
                )
            )
        )
    return render(request, "topic_modeling/topic_model_list.html", context)


def lexicon_list(request):
    context = {
        "lexicons" : [],
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index")]
    }
    for lexicon in get_objects_for_user(request.user, "topic_modeling.view_lexicon"):
        context["lexicons"].append(
            (
                lexicon,
                get_objects_for_user(
                    request.user,
                    "topic_modeling:view_labeledcollection",
                    klass=models.LabeledCollection.objects.filter(lexicon=lexicon)
                )
            )
        )
    return render(request, "topic_modeling/lexicon_list.html", context)


#TODO
def lexicon_detail(request, lid):
    context = {
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index")]
    }
    return render(request, "topic_modeling/lexicon_detail.html", context)


def topic_model_detail(request, mid):
    topic_model = models.TopicModel.objects.get(id=mid)
    model = pickle.loads(topic_model.serialized.tobytes())
    topics = [(tid + 1, model.show_topic(tid)) for tid in range(topic_model.topic_count)]
    context = {
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index")],
        "topic_model" : topic_model,
        "topics" : topics
    }
    return render(request, "topic_modeling/topic_model_detail.html", context)


def topic_model_topic_detail(request, mid, tid):
    context = {
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index")],
        "model" : models.TopicModel.objects.get(id=mid),
        "topic" : tid
    }
    return render(request, "topic_modeling/topic_model_topic_detail.html", context)


def labeled_document_detail(request, did):
    ld = LabeledDocument.objects.only("document__title", "content", "labeled_collection").select_related("document").get(id=did)
    j = json.loads(ld.content.tobytes())
    context = {
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index")],
        "labeled_document" : j,
        "title" : ld.document.title
    }
    return render(request, "topic_modeling/labeled_document_detail.html", context)


def labeled_collection_detail(request, lcid):
    lc = LabeledCollection.objects.get(id=lcid)
    context = {
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index")],
        "labeled_collection" : lc,
        "labeled_documents" : LabeledDocument.objects.only("id", "document__id").filter(labeled_collection=lc).select_related("document")
    }
    return render(request, "topic_modeling/labeled_collection_detail.html", context)


def vega_wordcloud(request, mid, tid):
    topic_model = models.TopicModel.objects.get(id=mid)
    model = pickle.loads(topic_model.serialized.tobytes())    
    words = model.show_topic(tid - 1, 50)
    retval = WordCloud(words)
    retval = retval.json
    return JsonResponse(retval)
