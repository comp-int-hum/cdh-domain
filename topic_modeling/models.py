import logging
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
try:
    from django.contrib.gis.db import models
except:
    from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator
from cdh import settings
from cdh.models import CdhModel, User, AsyncMixin, MetadataMixin
from cdh.decorators import cdh_cache_method, cdh_action
from primary_sources.models import Query, Annotation
import pickle
import json
import random
import requests
import time
from datetime import datetime
from django.core.files.base import ContentFile
from gensim.models import LdaModel
from gensim.corpora import Dictionary
from jsonpath import JSONPath
from spacy.lang import en
from gensim.models.callbacks import Metric
import requests
import gzip
import re
from rdflib import Graph, URIRef, Namespace, BNode, Literal
from rdflib.namespace import SH, RDF, RDFS, XSD, SDO
import rdflib
import uuid


CDH = Namespace("http://cdh.jhu.edu/materials/")


if settings.USE_CELERY:
    from celery import shared_task
else:
    def shared_task(func):
        return func


logger = logging.getLogger(__name__)


class Lexicon(CdhModel):
    lexical_sets = models.TextField()

    class Meta(CdhModel.Meta):
        pass

    @cdh_action(detail=True, methods=["post"])
    def apply(self, query_id, url, graph_name):
        #qid = int(query.rstrip("/").split("/")[-1])
        apply_lexicon_or_topicmodel.delay(query_id, url, graph_name, lexicon_id=self.id)
        return {"success" : True, "name" : "apply"}
    
    def clean(self):
        try:
            j = json.loads(self.lexical_sets)
        except:
            raise ValidationError({"lexical_sets" : "Invalid JSON"})
        if not isinstance(j, dict):
            raise ValidationError({"lexical_sets" : "Lexicon must be a JSON dictionary"})
        if len(j) == 0:
            raise ValidationError({"lexical_sets" : "Lexicon must have at least one lexical set"})
        for k, v in j.items():
            if not isinstance(v, list) or len(v) == 0:
                raise ValidationError({"lexical_sets" : "Each lexical set must be a non-empty list of strings (word-patterns)"})
            if not isinstance(k, str) or any([not isinstance(w, str) for w in v]):
                raise ValidationError({"lexical_sets" : "Word-patterns must be strings"})
        super(Lexicon, self).clean()


class TopicModel(AsyncMixin, CdhModel):
    topic_count = models.IntegerField(default=10, help_text="The number of topics to infer from the data")
    lowercase = models.BooleanField(default=True, help_text="Whether to convert text to lower-case")
    max_context_size = models.IntegerField(default=1000, help_text="If a document has more tokens than this, it will be split up into sub-documents")
    chunk_size = models.IntegerField(default=2000)
    maximum_vocabulary = models.IntegerField(default=5000, help_text="Only consider this number of most-frequent words in the data")
    minimum_occurrence = models.IntegerField(default=5, help_text="Ignore words that occur less than this number of times (often misspellings and other noise)")
    maximum_proportion = models.FloatField(default=0.5, help_text="Ignore words that occur in more than this proportion of documents (often function words and formatting)")
    passes = models.IntegerField(default=20)
    update_every = models.IntegerField(default=1)
    alpha = models.CharField(default="symmetric", choices=[("symmetric", "Symmetric"), ("asymmetric", "Asymmetric")], max_length=20)
    eta = models.CharField(default="symmetric", choices=[("symmetric", "Symmetric"), ("asymmetric", "Asymmetric")], max_length=20)
    iterations = models.IntegerField(default=40)
    random_seed = models.IntegerField(default=0)
    split_pattern = models.CharField(max_length=200, default=r"\s+")
    token_pattern_in = models.CharField(max_length=200, default=r"(\S+)")
    token_pattern_out = models.CharField(max_length=200, default=r"\1")
    query = models.ForeignKey(Query, on_delete=models.CASCADE, null=True, help_text="The primary source query to train on")
    serialized = models.BinaryField(null=True)
    maximum_documents = models.IntegerField(default=30000, help_text="Randomly choose this number of documents to train on (if the collection is larger)")
    
    @cdh_cache_method
    def topic_word_probabilities(self, num_words=50):
        if self.state != self.COMPLETE:
            return []
        model = pickle.loads(self.serialized) #.tobytes())
        words = sum(
            [
                [
                    {"word" : w, "probability" : float(p), "topic" : str(i + 1)} for w, p in model.show_topic(i, num_words)
                ] for i in range(model.num_topics)
            ],
            []
        )
        return words

    @cdh_action(detail=True, methods=["post"])
    def apply(self, query_id, url, graph_name):
        #query = Query.objects.get(id=query_id)
        #qid = int(query.rstrip("/").split("/")[-1])
        apply_lexicon_or_topicmodel.delay(query_id, url, graph_name, topicmodel_id=self.id)
        return {"success" : True}
        
    @cdh_action(detail=True, methods=["get"])
    def topics(self, num_words=8):
        ws = self.topic_word_probabilities(num_words)
        retval = {
            "column_names" : ["" for i in range(1, num_words + 1)],
            "row_names" : [str(i) for i in range(1, self.topic_count)],
            "column_label" : "Words in decreasing probability",
            "row_label" : "Topics",
            "rows" : []
        }
        for i in range(1, self.topic_count + 1):
            si = str(i)
            words = list(sorted([x for x in ws if x["topic"] == si], key=lambda x : x["probability"], reverse=True))[:num_words]
            retval["rows"].append(
                words
            )
        return retval

    @cdh_cache_method
    def topic_names(self, num_words=20):
        words = self.vega_words
        topic_names = {}
        for topic_id in range(self.topic_count):
            topic_words = [w for w in words if w["topic"] == str(topic_id + 1)]
            topic_names[topic_id + 1] = ", ".join([w["word"] for w in sorted(topic_words, key=lambda x : x["probability"], reverse=True)[:num_words]])
        return topic_names

    def save(self, **argd):
        update = self.id and True
        retval = super(TopicModel, self).save()
        if not update:
            train_model.delay(self.id, argd.get("url_field", "url"), argd.get("text_field", "text"), argd.get("remove_stopwords", True))
        return retval


class EpochLogger(Metric):
    logger = "cdh"
    title = "epochs"
    
    def __init__(self, obj, *argv, **argd):
        super(EpochLogger, self).__init__()
        self.epoch = 0
        self.object = obj
        self.set_epoch()

    def set_epoch(self):
        self.epoch += 1
        self.object.message = "On pass #{}/{}".format(self.epoch, self.object.passes)
        self.object.save()
        
    def get_value(self, *argv, **argd):
        self.set_epoch()
        return 0
    

@shared_task
def train_model(topicmodel_id, url_field, text_field, remove_stopwords):
    logging.info(topicmodel_id, url_field)
    time.sleep(2)
    topicmodel = TopicModel.objects.get(id=topicmodel_id)
    
    primarysource = topicmodel.query.primarysource
    while primarysource.state == primarysource.PROCESSING:
        time.sleep(10)
        primarysource = PrimarySource.objects.get(id=primarysource.id)

    topicmodel.message = "Preparing training data"
    topicmodel.save()
    #collection = topicmodel.collection
    random.seed(topicmodel.random_seed)
    try:
        results = []
        for hit in topicmodel.query.perform()["results"]["bindings"]:
            url = hit[url_field]["value"]
            prefix, name = url.split("/")[-2:]
            if name.endswith("jsonl.gz"):
                resp = requests.get(
                    "http://{}:{}/materials/{}/{}/".format(settings.HOSTNAME, settings.PORT, prefix, name),
                    stream=True
                    #auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
                )
                with gzip.open(resp.raw) as ifd:
                    for line in ifd:
                        j = json.loads(line)
                        results.append({"text" : j[text_field]})
            else:
                results.append({"url" : url})

        random.shuffle(results)
        logger.info("Loading %d documents and will randomly select a subset of %d", len(results), topicmodel.maximum_documents)
        docs = []
        for result in results[:topicmodel.maximum_documents]: #range(len(results)):
            if "text" in result:
                text = result["text"]
            else:
                prefix, name = result["url"].split("/")[-2:]
                resp = requests.get(
                    "http://{}:{}/materials/{}/{}/".format(settings.HOSTNAME, settings.PORT, prefix, name),
                    #auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
                )
                text = resp.content.decode("utf-8")
            text = text.lower() if topicmodel.lowercase else text
            toks = [re.sub(topicmodel.token_pattern_in, topicmodel.token_pattern_out, t) for t in re.split(topicmodel.split_pattern, text) if (not remove_stopwords) or (t.lower() not in en.stop_words.STOP_WORDS)]
            num_subdocs = round(0.5 + len(toks) / topicmodel.max_context_size)
            if num_subdocs == 0:
                continue
            toks_per = int(len(toks) / num_subdocs)
            for i in range(num_subdocs):
                docs.append(toks[i * toks_per : (i + 1) * toks_per])
        logger.info("Loaded %d subdocuments", len(docs))
        dictionary = Dictionary(docs)
        dictionary.filter_extremes(no_below=topicmodel.minimum_occurrence, no_above=topicmodel.maximum_proportion, keep_n=topicmodel.maximum_vocabulary)
        corpus = [dictionary.doc2bow(doc) for doc in docs]
        el = EpochLogger(topicmodel)
        model = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=topicmodel.topic_count,
            alpha="auto",
            eta="auto",
            iterations=topicmodel.iterations,
            passes=topicmodel.passes,
            random_state=topicmodel.random_seed,
            eval_every=None,
            callbacks=[el],
        )
        topicmodel.state = topicmodel.COMPLETE
        topicmodel.serialized = pickle.dumps(model)
    except Exception as e:
        topicmodel.state = topicmodel.ERROR
        topicmodel.message = "{}".format(e)
        raise e
    topicmodel.message = ""
    topicmodel.save()


def topicmodel_label(topicmodel, gensim_model, text):
    toks = [re.sub(topicmodel.token_pattern_in, topicmodel.token_pattern_out, t) for t in re.split(topicmodel.split_pattern, text)]
    num_subdocs = round(0.5 + len(toks) / topicmodel.max_context_size)
    toks_per = int(len(toks) / num_subdocs)
    labeled_toks = []
    topic_counts = {}
    for i in range(num_subdocs):
        orig_subdoc_toks = toks[i * toks_per : (i + 1) * toks_per]
        subdoc_toks = [t.lower() for t in orig_subdoc_toks] if topicmodel.lowercase else orig_subdoc_toks
        _, text_topics, _ = gensim_model.get_document_topics(gensim_model.id2word.doc2bow(subdoc_toks), per_word_topics=True)
        word2topic = {gensim_model.id2word[wid] : -1 if len(topics) == 0 else topics[0] for wid, topics in text_topics}
        content = [(o, word2topic.get(t, -1)) for o, t in zip(orig_subdoc_toks, subdoc_toks)]
        for _, t in content:
            if t != -1:
                topic_counts[t + 1] = topic_counts.get(t + 1, 0) + 1
    return topic_counts


def lexicon_label(lexicon, text):
    lexical_sets = {name : "^({})$".format("|".join(terms)) for name, terms in lexicon.items()}
    toks = re.split(r"\s+", text)
    num_subdocs = round(0.5 + len(toks) / 2000)
    toks_per = int(len(toks) / num_subdocs)
    labeled_toks = []
    topic_counts = {}
    for i in range(num_subdocs):
        subdoc_toks = toks[i * toks_per : (i + 1) * toks_per]
        content = [(t, [k for k, v in lexical_sets.items() if re.match(v, t, re.I)]) for t in subdoc_toks]
        content = [(o, v[0]) for o, v in content if len(v) > 0]
        for _, t in content:
            topic_counts[t] = topic_counts.get(t, 0) + 1            
    return topic_counts


@shared_task
def apply_lexicon_or_topicmodel(query_id, url, graph_name, lexicon_id=None, topicmodel_id=None, url_field="url", text_field="text"):
    query = Query.objects.get(id=query_id)
    primarysource = query.primarysource
    while primarysource.state == primarysource.PROCESSING:
        time.sleep(10)
        primarysource = PrimarySource.objects.get(id=primarysource.id)
    annotation_graph = Graph()
    annotation_graph.bind("cdh", CDH)
    ann_node = BNode()
    mod_node = BNode()
    topic_uris = {}
    if lexicon_id:
        lexicon = Lexicon.objects.get(id=lexicon_id)
        labeler = json.loads(lexicon.lexical_sets)
        labeler_type = "lexicon"
        labeler_id = lexicon.id
        topics = {k : [{"word" : w} for w in v] for k, v in labeler.items()}
        for k, v in labeler.items():
            topic_uris[k] = BNode()
            annotation_graph.add(
                (
                    mod_node,
                    SDO.option,
                    topic_uris[k]
                )
            )
            for w in v:
                lex_node = BNode()
                annotation_graph.add(
                    (
                        topic_uris[k],
                        SDO.hasPart,
                        lex_node
                    )
                )
                annotation_graph.add(
                    (
                        lex_node,
                        SDO.name,
                        Literal(w)
                    )
                )                
    else:
        topicmodel = TopicModel.objects.get(id=topicmodel_id)
        while topicmodel.state == topicmodel.PROCESSING:
            time.sleep(10)
            topicmodel = TopicModel.objects.get(id=topicmodel.id)

        labeler = pickle.loads(topicmodel.serialized)
        labeler_id = topicmodel.id
        labeler_type = "topicmodel"
        topics = [
            [
                {"word" : w, "probability" : float(p)} for w, p in labeler.show_topic(i, 1000)
            ] for i in range(labeler.num_topics)
        ]
        for i in range(1, topicmodel.topic_count + 1):
            topic_uris[i] = BNode()
            #for k, v in labeler.items():
            #topic_uris[k] = BNode()
            annotation_graph.add(
                (
                    mod_node,
                    SDO.option,
                    topic_uris[i]
                )
            )
            for w in topics[i - 1]:
                lex_node = BNode()
                annotation_graph.add(
                    (
                        topic_uris[i],
                        SDO.hasPart,
                        lex_node
                    )
                )
                annotation_graph.add(
                    (
                        lex_node,
                        SDO.name,
                        Literal(w["word"])
                    )
                )
                annotation_graph.add(
                    (
                        lex_node,
                        SDO.value,
                        Literal(w["probability"])
                    )
                )


            
    annotation_graph.add(
        (
            ann_node,
            RDF.type,
            SDO.Action
        )
    )
    annotation_graph.add(
        (
            ann_node,
            SDO.instrument,
            mod_node
        )
    )
    annotation_graph.add(
        (
            mod_node,
            SDO.identifier,
            Literal(labeler_id)
        )
    )
    annotation_graph.add(
        (
            mod_node,
            SDO.disambiguatingDescription,
            Literal(labeler_type)
        )
    )
    for k, v in topic_uris.items():
        annotation_graph.add(
            (
                mod_node,
                SDO.option,
                v
            )
        )
        annotation_graph.add(
            (
                v,
                SDO.description,
                Literal(k)
            )
        )
        
    for hit in query.perform()["results"]["bindings"]:
        u = hit[url_field]["value"]
        prefix, name = u.split("/")[-2:]
        resp = requests.get(
            "http://{}:{}/materials/{}/{}/".format(settings.HOSTNAME, settings.PORT, prefix, name),
            stream=True
        )        
        if name.endswith("jsonl.gz"):
            with gzip.open(resp.raw) as ifd:
                for i, line in enumerate(ifd):
                    if i > 5000:
                        break
                    j = json.loads(line)
                    text = j[text_field]
                    topic_counts = topicmodel_label(topicmodel, labeler, text) if topicmodel_id else lexicon_label(labeler, text)
                    sub_uri = BNode()
                    annotation_graph.add(
                        (
                            ann_node,
                            SDO.hasPart,
                            sub_uri
                        )
                    )
                    annotation_graph.add(
                        (
                            sub_uri,
                            SDO.identifier,
                            Literal(i)
                        )
                    )
                    for k, v in topic_counts.items():
                        topic_label_node = BNode()
                        annotation_graph.add(
                            (
                                sub_uri,
                                SDO.hasPart,
                                topic_label_node
                            )
                        )
                        annotation_graph.add(
                            (
                                topic_label_node,
                                RDF.type,
                                SDO.PropertyValue
                            )
                        )
                        annotation_graph.add(
                            (
                                topic_label_node,
                                SDO.propertyID,
                                topic_uris[k]
                            )
                        )
                        annotation_graph.add(
                            (
                                topic_label_node,
                                SDO.value,
                                Literal(v)
                            )
                        )
        else:
            text = resp.raw.read()
            topic_counts = topicmodel_label(topicmodel, labeler, text) if topicmodel_id else lexicon_label(labeler, text)
            sub_uri = BNode()
            annotation_graph.add(
                (
                    ann_node,
                    SDO.hasPart,
                    sub_uri
                )
            )
            topic_uris = {}
            for k, v in topic_counts.items():
                pass


            results.append({"url" : u})

    resp = requests.put(
        url,
        params={"graph" : graph_name},
        headers={"default" : "", "Content-Type" : "text/turtle"},
        data=annotation_graph.serialize(format="turtle").encode("utf-8"),
        auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)                    
    )
