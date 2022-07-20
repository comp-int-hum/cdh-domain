import pickle
import gzip
import json
import logging
from datetime import datetime
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView, TemplateView, DetailView
from django.urls import reverse
from guardian.shortcuts import get_objects_for_user
from django.contrib.auth.decorators import login_required
from . import models
from . import forms
from . import tasks
from gensim.models import LdaModel
from gensim.corpora import Dictionary
from .vega import TopicModelWordCloud, TemporalEvolution, SpatialDistribution
from .models import TopicModel, LabeledCollection, Lexicon, Collection, LabeledDocument, Document, LabeledDocumentSection
from .forms import CollectionCreateForm, LexiconForm
from django.utils.safestring import mark_safe
from django.http import JsonResponse
from django.core.paginator import Paginator
from topic_modeling import apps
from django.views.generic.detail import TemplateResponseMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView, ModelFormMixin, DeletionMixin, ProcessFormView
from django.views import View
from cdh.widgets import VegaWidget
from .vega import TopicModelWordCloud


class CollectionCreateView(TemplateResponseMixin, ProcessFormView, View):
    form_class = CollectionCreateForm
    model = Collection
    template_name = "cdh/simple_interface.html"
    def __init__(self, *argv, **argd):
        return super(CollectionCreateView, self).__init__(*argv, **argd)
    def get(self, request, *argv, **argd):
        return render(request, self.template_name, {})


class WordTableView(SingleObjectMixin, View):
    template_name = "cdh/simple_interface.html"
    show = 6
    def render(self, request):
        topics = {}
        for item in self.get_object().vega_words:
            word = item["word"]
            topic = int(item["topic"])
            prob = float(item["probability"])
            topics[topic] = topics.get(topic, [])
            topics[topic].append((prob, word))
        topics = {k : sorted(v, reverse=True) for k, v in topics.items()}
        header_content = "<th scope='col'>Topic</th>" + "".join(["<th scope='col'/>" for i in range(self.show)])
        rows = ["<tr><td>{topic}</td>{cells}</tr>".format(
            topic=num,
            cells="".join(["<td>{}<br/>{:.3}</td>".format(w, p) for p, w in words[:self.show]])
        ) for num, words in sorted(topics.items())]
        
        retval = """
        <table class="table">
        <thead>
        <tr>{header_content}</tr>
        </thead>
        <tbody>
        {row_content}
        </tbody>
        </table>
        """.format(
            header_content=header_content,
            row_content="\n".join(rows)
        )
        print(retval)
        return mark_safe(retval)
    
    def get(self, request, *argv, **argd):
        return render(request, self.template_name, {"content" : self.render(request)})
