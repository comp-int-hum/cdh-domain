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
from .models import TopicModel, Output, Lexicon, Collection
from django.http import JsonResponse

@login_required(login_url="/accounts/login/")
def index(request):
    context = {
        "collections" : get_objects_for_user(request.user, "topic_modeling.view_collection"),
        "topic_models" : get_objects_for_user(request.user, "topic_modeling.view_topicmodel"),
        #"lexicons" : get_objects_for_user(request.user, "topic_modeling.view_lexicon"),
        "outputs" : get_objects_for_user(request.user, "topic_modeling.view_output"),
    }
    return render(request, "topic_modeling/index.html", context)

@login_required(login_url="/accounts/login/")
def topic_model_detail(request, mid):
    topic_model = models.TopicModel.objects.get(id=mid)
    model = LdaModel.load(topic_model.disk_serialized.path)
    topics = [(tid + 1, model.show_topic(tid)) for tid in range(topic_model.topic_count)]
    print(topics[0])
    context = {
        "topic_model" : topic_model,
        "topics" : topics
    }
    return render(request, "topic_modeling/topic_model_detail.html", context)

@login_required(login_url="/accounts/login/")
def output_detail(request, oid):
    #topic_model = models.TopicModel.objects.get(id=mid)
    #model = LdaModel.load(topic_model.disk_serialized.path)
    #topics = [(tid + 1, model.show_topic(tid)) for tid in range(topic_model.topic_count)]
    #print(topics[0])
    lookup = {
        0 : "first",
        1 : "second",
        2 : "third",
        3 : "fourth",
        4 : "fifth",
        5 : "sixth",
        6 : "seventh",
        7 : "eighth",
        8 : "ninth",
        9 : "tenth"
    }
    documents = []
    output = models.Output.objects.get(id=oid)
    with gzip.open(output.disk_serialized.path, "rt") as ifd:
        for line in ifd:
            document = []
            prev = None
            cur = []
            for w, t in json.loads(line):
                if prev != None and t != prev:
                    document.append((lookup.get(t, "other"), cur))
                    cur = [w]
                else:
                    cur.append(w)
                prev = t
            documents.append([(c, " ".join(ws)) for c, ws in document])
    context = {
        "output" : output,
        "documents" : documents,
    }
    return render(request, "topic_modeling/output_detail.html", context)

@login_required(login_url="/accounts/login/")
def wordcloud(request, mid, tid):
    return render(
        request,
        "topic_modeling/wordcloud.html",
        {
            "model": models.TopicModel.objects.get(id=mid),
            "tid": tid,
        }
    )

@login_required(login_url="/accounts/login/")
def vega_topics(request, mid, tid):
    tm = models.TopicModel.objects.get(id=mid)
    tm = LdaModel.load(tm.disk_serialized.path)
    words = tm.show_topic(tid - 1, 50)
    retval = WordCloud(words)
    retval = retval.json
    return JsonResponse(retval)


#@login_required(login_url="/accounts/login/")
#def word(request, word):
#    context = {
#        "word": word
#    }
#    return render(request, "topic_modeling/word_filler.html", context)
