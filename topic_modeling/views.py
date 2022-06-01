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
from .vega import WordCloud, TemporalEvolution, SpatialDistribution
from .models import TopicModel, LabeledCollection, Lexicon, Collection, LabeledDocument, Document, LabeledDocumentSection
from django.http import JsonResponse
from django.core.paginator import Paginator
from topic_modeling import apps
# TODO: needs pagination, breadcrumbs


def index(request):
    context = {
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index", None)],
        "topic_models" : get_objects_for_user(request.user, "topic_modeling.view_topicmodel"),
    }
    return render(request, "topic_modeling/index.html", context)


def collection_list(request):
    context = {
        "collections" : [],
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index", None), ("By collection", "topic_modeling:collection_list", None)]
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
        "breadcrumbs" : [
            ("Topic modeling", "topic_modeling:index", None),
            ("By model", "topic_modeling:topic_model_list", None),
        ]
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
        "breadcrumbs" : [
            ("Topic modeling", "topic_modeling:index", None),
            ("Lexicons", "topic_modeling:lexicon_list", None),
        ]
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
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index", None)]
    }
    return render(request, "topic_modeling/lexicon_detail.html", context)


def topic_model_detail(request, mid):
    topic_model = models.TopicModel.objects.get(id=mid)
    model = pickle.loads(topic_model.serialized.tobytes())
    lcs = get_objects_for_user(
        request.user,
        "topic_modeling:view_labeledcollection",
        klass=models.LabeledCollection.objects.filter(model=topic_model),
    )
    topics = [(tid + 1, model.show_topic(tid)) for tid in range(topic_model.topic_count)]
    context = {
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index", None)],
        "topic_model" : topic_model,
        "topics" : topics,
        "labeled_collections" : lcs,
    }
    return render(request, "topic_modeling/topic_model_detail.html", context)


def topic_model_topic_detail(request, mid, tid):
    context = {
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index", None)],
        "model" : models.TopicModel.objects.get(id=mid),
        "topic" : tid
    }
    return render(request, "topic_modeling/topic_model_topic_detail.html", context)


def labeled_document_detail(request, did):
    ld = LabeledDocument.objects.only("document__title", "labeled_collection").select_related("document").get(id=did)
    lds = LabeledDocumentSection.objects.filter(labeled_document=ld).order_by("id")
    paginator = Paginator(lds, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        "breadcrumbs" : [("Topic modeling", "topic_modeling:index", None)],
        "page_obj" : page_obj,
        "title" : ld.document.title
    }
    return render(request, "topic_modeling/labeled_document_detail.html", context)


def labeled_collection_detail(request, lcid):
    lc = LabeledCollection.objects.get(id=lcid)
    context = {
        "breadcrumbs" : [
            ("Topic modeling", "topic_modeling:index", None),
            ("By collection", "topic_modeling:collection_list", None),
            (lc.collection.name, "topic_modeling:labeled_collection_detail", lc.id),
        ],
        "labeled_collection" : lc,
        "labeled_documents" : LabeledDocument.objects.only("id", "document__id").filter(labeled_collection=lc).select_related("document")
    }
    return render(request, "topic_modeling/labeled_collection_detail.html", context)


def spatial(request, lcid):
    lc = models.LabeledCollection.objects.get(id=lcid)
    context = {
        "breadcrumbs" : [
            ("Topic modeling", "topic_modeling:index", None),
            ("By model", "topic_modeling:topic_model_list", None),
            ("Spatial view of {}".format(lc.name), "topic_modeling:spatial_evolution", lcid),
        ],
        "labeled_collection" : lc,
    }
    return render(request, "topic_modeling/spatial_evolution.html", context)


def temporal(request, lcid):
    lc = models.LabeledCollection.objects.get(id=lcid)
    context = {
        "breadcrumbs" : [
            ("Topic modeling", "topic_modeling:index", None),
            ("By model", "topic_modeling:topic_model_list", None),
            ("Temporal view of {}".format(lc.name), "topic_modeling:temporal_evolution", lcid),
        ],
        "labeled_collection" : lc,
    }
    return render(request, "topic_modeling/temporal_evolution.html", context)


def vega_wordcloud(request, mid, tid):
    topic_model = models.TopicModel.objects.get(id=mid)
    model = pickle.loads(topic_model.serialized.tobytes())    
    words = model.show_topic(tid - 1, 50)
    retval = WordCloud(words)
    retval = retval.json
    return JsonResponse(retval)


def vega_spatial(request, lcid):
    lc = models.LabeledCollection.objects.get(id=lcid)
    vs = models.TemporalEvolution.objects.filter(labeled_collection=lc)
    model = pickle.loads(lc.model.serialized.tobytes())    
    topics = dict([(tid, model.show_topic(tid)) for tid in range(lc.model.topic_count)])
    coordinates = []
    for ld in models.LabeledDocument.objects.filter(labeled_collection=lc):
        counts = {int(k) : v for k, v in ld.metadata["topic_counts"].items()}
        total = sum(counts.values())
        for t, v in counts.items():
            coordinates.append(
                {
                    "topic" : t,
                    "weight" : v / total,
                    "latitude" : ld.document.latitude,
                    "longitude" : ld.document.longitude,
                }
            )
    retval = SpatialDistribution(coordinates)
    retval = retval.json
    return JsonResponse(retval)


def vega_temporal(request, lcid):
    lc = models.LabeledCollection.objects.get(id=lcid)
    vs = models.TemporalEvolution.objects.filter(labeled_collection=lc)
    model = pickle.loads(lc.model.serialized.tobytes())    
    topics = dict([(tid, model.show_topic(tid)) for tid in range(lc.model.topic_count)])
    if vs.count() == 0:
        min_time, max_time = None, None        
        vals = []
        for ld in models.LabeledDocument.objects.filter(labeled_collection=lc):
            time = ld.document.year
            min_time = time if min_time == None else min(min_time, time)
            max_time = time if max_time == None else max(max_time, time)
            vals.append((time, {int(k) : v for k, v in ld.metadata["topic_counts"].items()}))
        duration = 10
        minimum = 1550
    else:
        pass
    all_years = set()
    all_labels = set()
    buckets = {}
    years = {}
    year_totals = {}
    for year, counts in vals:
        year = year - (year % duration)
        if year < 1550:
            continue
        all_years.add(year)
        buckets[year] = buckets.get(year, 0) + 1
        for k, v in counts.items():
            label = ", ".join([w for w, _ in topics[k][0:10]])
            all_labels.add(label)
            years[year] = years.get(year, {})
            years[year][label] = years[year].get(label, 0.0) + v
            year_totals[year] = year_totals.get(year, 0.0) + v

    for label in all_labels:
        for year in all_years:
            if label not in years[year]:
                print(year, label)
            years[year][label] = years[year].get(label, 0.0)

    data = sum(
        [
            [
                {
                    "label" : label,
                    "value" : value / year_totals[year],
                    "year" : year
                } for label, value in labels.items()] for year, labels in years.items()
        ],
        []
    )
    retval = TemporalEvolution(data)
    return JsonResponse(retval.json)
