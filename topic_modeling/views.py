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

@login_required(login_url="/accounts/login/")
def index(request):
    context = {
        "collections" : get_objects_for_user(request.user, "topic_modeling.view_collection"),
        "collection_form" : forms.CollectionForm(),
        "models" : get_objects_for_user(request.user, "topic_modeling.view_topicmodel"),
        "model_form" : forms.TopicModelForm(),
        "lexicons" : get_objects_for_user(request.user, "topic_modeling.view_lexicon"),
        "lexicon_form" : forms.LexiconForm(),
        "outputs" : get_objects_for_user(request.user, "topic_modeling.view_output"),
        "output_form" : forms.OutputForm(),
    }
    return render(request, "topic_modeling/collection_list.html", context)

@login_required(login_url="/accounts/login/")
def topic_model_list(request):
    pass

@login_required(login_url="/accounts/login/")
def lexicon_list(request):
    pass

@login_required(login_url="/accounts/login/")
def lexicon_detail(request, lid):
    pass

@login_required(login_url="/accounts/login/")
def output_list(request):
    pass

@login_required(login_url="/accounts/login/")
def output_detail(request, oid):
    pass

@login_required(login_url="/accounts/login/")
def collection_list(request):
    if request.method == "POST":
        data = request.FILES.get("data")
        name = request.POST.get("name")
        if name and data:
            collection = models.Collection(name=name, created_by=request.user, data=data)
            collection.save()
            tasks.extract_documents.delay(collection.id)
        for k, v in request.POST.items():
            if v == "on":
                cid = int(k.split("_")[-1])
                coll = models.Collection.objects.get(id=cid)
                coll.data.delete()
                coll.delete()
        return HttpResponseRedirect(reverse("topic_modeling:collection_list"))
    else:
        context = {
            "user_collections" : models.Collection.objects.filter(created_by=request.user),
            "public_collections" : models.Collection.objects.filter(public=True)
        }
        return render(request, 'topic_modeling/collection_list.html', context)

@login_required(login_url="/accounts/login/")
def document_detail(request, did):
    context = {
        "document" : models.Document.objects.get(id=did)
    }
    return render(request, 'topic_modeling/document_detail.html', context)    
    
@login_required(login_url="/accounts/login/")
def collection_detail(request, cid):
    collection = models.Collection.objects.get(id=cid)
    if request.method == "POST":
        print(request.POST)
        name = request.POST.get("name")
        topic_count = request.POST.get("topic_count")
        if name and topic_count:
            tmf = forms.TopicModelForm(request.POST)
            topic_model = tmf.save()
            topic_model.created_by = request.user
            topic_model.collection = collection
            topic_model.state = topic_model.PROCESSING
            topic_model.save()
            task = tasks.train_model.delay(topic_model.id)
        else:
            for k, v in request.POST.items():
                if v == "on":
                    mid = int(k.split("_")[-1])
                    model = models.TopicModel.objects.get(id=mid)
                    for ext in [".expElogbeta.npy", ".id2word", ".state"]:
                        os.remove("{}{}".format(model.data.path, ext))
                    model.data.delete()
                    model.delete()
        return HttpResponseRedirect(collection.get_absolute_url())
    else:
        context = {
            "form" : forms.TopicModelForm,
            "collection" : collection,
            "documents" : models.Document.objects.filter(collection=collection),
            "topic_models" : models.TopicModel.objects.filter(collection=collection),
        }
        return render(request, 'topic_modeling/collection_detail.html', context)

@login_required(login_url="/accounts/login/")
def topic_model_detail(request, mid):
    topic_model = models.TopicModel.objects.get(id=mid)
    model = LdaModel.load(topic_model.data.path)
    topics = model.show_topics(num_topics=model.num_topics, formatted=False)
    context = {"topic_model" : topic_model,
               "topics" : topics
               }
    return render(request, "topic_modeling/topic_model_detail.html", context)

