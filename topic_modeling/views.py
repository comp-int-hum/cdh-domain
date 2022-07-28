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
from django.utils.text import slugify


class WordTableView(SingleObjectMixin, View):
    template_name = "cdh/simple_interface.html"
    show = 8
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
        return mark_safe(retval)
    
    def get(self, request, *argv, **argd):
        return render(request, self.template_name, {"content" : self.render(request), "preamble" : """
        Each row in the table corresponds to a topic inferred by the model, and shows the most-likely words
        that an author would use to express that topic.  The number underneath each word is the probability
        of that word being written, assuming that topic is being expressed.
        """})


class LabeledDocumentView(SingleObjectMixin, View):
    template_name = "cdh/simple_interface.html"
    model = LabeledDocument
    section_model = LabeledDocumentSection

    def render(self, request):
        obj = self.get_object()
        toks = []
        for section in self.section_model.objects.filter(labeleddocument=obj):
            for w, t in section.content:
                if t == -1:
                    toks.append("""<span class="labeled-token">{}</span>""".format(w))
                else:
                    toks.append("""<span class="labeled-token topic-{}">{}</span>""".format(t, w))
        retval = """
        <div class="card">
        <div class="card-body">
        <!--<h5 class="card-title">{{title}}</h5>-->
        <div class="container">
        <p>
        {}dasdas
        </p>
        </div>
        </div>
        </div>
        """.format(
            " ".join(toks)
        )
        return mark_safe(retval)
    
    def get(self, request, *argv, **argd):
        return render(request, self.template_name, {"content" : self.render(request)})
