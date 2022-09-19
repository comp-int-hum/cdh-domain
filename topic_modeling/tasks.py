import io
import time
from cdh import settings
import zipfile
import random
import pickle
import json
import csv
import gzip
import logging
import re
import os
import tarfile
import tempfile
from datetime import datetime
from django.core.files.base import ContentFile
from . import models
from gensim.models import LdaModel
from gensim.corpora import Dictionary
from jsonpath import JSONPath
from spacy.lang import en
from gensim.models.callbacks import Metric
import requests
from .models import User

if settings.USE_CELERY:
    from celery import shared_task
else:
    def shared_task(func):
        return func


logger = logging.getLogger(__name__)
    
    
def process_zip(fname):
    with zipfile.ZipFile(fname) as ifd:
        names = ifd.namelist()
        c_fnames = [n for n in names if n.endswith("csv")]
        metadata = {}
        if len(c_fnames) == 1:            
            c = csv.DictReader(io.TextIOWrapper(ifd.open(c_fnames[0])), delimiter=",")
            for row in c:
                metadata[row["file_name"]] = {k : v for k, v in row.items() if k != "file_name"}
        for a_fname in names:
            if a_fname.endswith("txt"):
                item = metadata.get(a_fname, {})                
                item["text"] = ifd.open(a_fname).read()
                item["title"] = item.get("title", a_fname)                
                yield item


def process_tar(fname):
    with tarfile.open(fname, "r") as ifd:
        names = ifd.getnames()
        c_fnames = [n for n in names if n.endswith("csv")]
        metadata = {}
        if len(c_fnames) == 1:
            c = csv.DictReader(io.TextIOWrapper(ifd.extractfile(c_fnames[0])), delimiter=",")
            for row in c:
                metadata[row["file_name"]] = {k : v for k, v in row.items() if k != "file_name"}
        for a_fname in names:
            if a_fname.endswith("txt"):
                item = metadata.get(a_fname, {})                
                item["text"] = ifd.extractfile(a_fname).read()
                item["title"] = item.get("title", a_fname)
                yield item
                

def process_json(fname):
    with (gzip.open if fname.endswith("gz") else open)(fname, "rt") as ifd:
        c = None
        while c not in ["{", "["]:
            c = ifd.read(1)
        if c == None:
            raise Exception("Couldn't find straight or curly bracket")
        else:
            stream = c == "{"
    with (gzip.open if fname.endswith("json.gz") else open)(fname, "rt") as ifd:
        if stream:
            for line in ifd:
                yield json.loads(line)
        else:
            for j in json.loads(ifd.read()):
                yield j
                
            
def process_csv(fname):
    with (gzip.open if fname.endswith("gz") else open)(fname, "rt") as ifd:
        c = csv.DictReader(ifd, delimiter=",")
        for row in c:
            yield row

    
# This needs to be modular
@shared_task
def extract_documents(
        collection_id,
        fname,
        **argd
):
    title_field = JSONPath(argd["title_field"][0])
    author_field = JSONPath(argd["author_field"][0])
    temporal_field = JSONPath(argd["temporal_field"][0])
    spatial_field = JSONPath(argd["spatial_field"][0])
    text_field = JSONPath(argd["text_field"][0])
    lang_field = JSONPath(argd["language_field"][0])
    time.sleep(2)
    collection = models.Collection.objects.get(id=collection_id)
    collection.message = "Preparing to extract documents"
    collection.save()
    handler = process_zip if fname.endswith("zip") else process_csv if fname.endswith("csv") or fname.endswith("csv.gz") else process_json if fname.endswith("json") or fname.endswith("json.gz") else process_tar if fname.endswith("tar") or fname.endswith("tar.gz") else None
    has_temporality = False
    has_spatiality = False
    try:
        if handler == None:
            raise Exception("No handler for file '{}'".format(fname))
        else:
            for i, item in enumerate(handler(fname)):
                temporal = temporal_field.parse(item)
                spatial = spatial_field.parse(item)
                if len(temporal) > 0:
                    temporal = datetime.fromtimestamp(float(temporal[0]) / 1000)
                if len(spatial) > 0:
                    spatial = spatial[0]
                if temporal:
                    has_temporality = True
                if spatial:
                    has_spatiality = True
                title = title_field.parse(item)
                author = author_field.parse(item)
                text = text_field.parse(item)
                lang = lang_field.parse(item)
                if i % 1000 == 0:
                    collection.message = "{} document processed".format(i)
                    collection.save()
                docobj = models.Document(
                    name=title[0] if len(title) > 0 else "",
                    text=text[0] if len(text) > 0 else "",
                    language = lang[0][:2] if len(lang) > 0 else "",
                    spatial=spatial,
                    author=author[0] if len(author) > 0 else "",
                    collection=collection,
                )
                if temporal:
                    docobj.temporal = temporal                
                docobj.save()       
            collection.state = collection.COMPLETE
    except Exception as e:
        collection.state = collection.ERROR
        collection.message = str(e)        
        raise e
    finally:
        os.remove(fname)
    collection.has_temporality = has_temporality
    collection.has_spatiality = has_spatiality
    collection.save()


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
def train_model(topic_model_id, *argv, **argd):
    logging.info(topic_model_id, argv, argd)
    time.sleep(2)
    topic_model = models.TopicModel.objects.get(id=topic_model_id)
    topic_model.message = "Preparing training data"
    topic_model.save()
    #collection = topic_model.collection
    random.seed(topic_model.random_seed)
    try:
        docs = []
        if topic_model.query:
            results = [{"url" : x["url"]["value"]} for x in topic_model.query.perform()["results"]["bindings"]]
            random.shuffle(results)
            logger.info("Loading %d documents with an upper limit of %d", len(results), topic_model.maximum_documents)
            for result in results[:topic_model.maximum_documents]: #range(len(results)):
                prefix, name = result["url"].split("/")[-2:]            
                resp = requests.get(
                    "http://{}:{}/materials/{}/{}/".format(settings.HOSTNAME, settings.PORT, prefix, name),
                    auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
                )
                text = resp.content.decode("utf-8")
                text = text.lower() if topic_model.lowercase else text
                toks = [re.sub(topic_model.token_pattern_in, topic_model.token_pattern_out, t) for t in re.split(topic_model.split_pattern, text) if t.lower() not in en.stop_words.STOP_WORDS]
                num_subdocs = round(0.5 + len(toks) / topic_model.max_context_size)
                toks_per = int(len(toks) / num_subdocs)
                logger.info("Loading %s", name)
                for i in range(num_subdocs):
                    docs.append(toks[i * toks_per : (i + 1) * toks_per])                
        else:
            pass
            # logger.info("Querying documents")
            # qs = models.Document.objects.filter(collection=collection).only("id")
            # logger.info("Making indices")        
            # indices = list(range(qs.count()))
            # logger.info("Shuffling indices")
            # random.shuffle(indices)
            # logger.info("Selecting %d indices", topic_model.maximum_documents)
            # indices = set(indices[:topic_model.maximum_documents])
            # logger.info("Iterating documents")            
            # for i, doc in enumerate(qs): #enumerate(models.Document.objects.filter(collection=collection)):
            #     if i in indices:
            #         text = doc.text.lower() if topic_model.lowercase else doc.text
            #         toks = [re.sub(topic_model.token_pattern_in, topic_model.token_pattern_out, t) for t in re.split(topic_model.split_pattern, text) if t.lower() not in en.stop_words.STOP_WORDS]
            #         num_subdocs = round(0.5 + len(toks) / topic_model.max_context_size)
            #         toks_per = int(len(toks) / num_subdocs)
            #         for i in range(num_subdocs):
            #             docs.append(toks[i * toks_per : (i + 1) * toks_per])                
        logger.info("Loaded %d subdocuments", len(docs))
        dictionary = Dictionary(docs)
        dictionary.filter_extremes(no_below=topic_model.minimum_occurrence, no_above=topic_model.maximum_proportion, keep_n=topic_model.maximum_vocabulary)
        corpus = [dictionary.doc2bow(doc) for doc in docs]
        el = EpochLogger(topic_model)
        model = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=topic_model.topic_count,
            alpha="auto",
            eta="auto",
            iterations=topic_model.iterations,
            passes=topic_model.passes,
            random_state=topic_model.random_seed,
            eval_every=None,
            callbacks=[el],
        )
        topic_model.state = topic_model.COMPLETE
        topic_model.serialized = pickle.dumps(model)
    except Exception as e:
        topic_model.state = topic_model.ERROR
        topic_model.message = "{}".format(e)
        raise e
    topic_model.message = ""
    topic_model.save()


@shared_task
def apply_model(labeledcollection_id, user_id):
    user = User.objects.get(id=user_id)
    time.sleep(2)
    labeledcollection = models.LabeledCollection.objects.get(id=labeledcollection_id)
    labeledcollection.message = "Preparing to label documents"
    labeledcollection.save()
    try:
        number_labeled = 0        
        if labeledcollection.lexicon:
            lexicon = json.loads(labeledcollection.lexicon.lexical_sets)
            cache = {}
            lexical_sets = {name : "^({})$".format("|".join(terms)) for name, terms in lexicon.items()}
            for j, doc in enumerate(models.Document.objects.only("id").filter(collection=labeledcollection.collection)):
                if j not in indices:
                    continue
                labeled_doc = models.LabeledDocument(
                    document=doc,
                    labeledcollection=labeledcollection,
                    created_by=user,
                )
                labeled_doc.save()
                text = doc.text
                toks = re.split(r"\s+", text)
                num_subdocs = round(0.5 + len(toks) / 2000)
                toks_per = int(len(toks) / num_subdocs)
                labeled_toks = []
                topic_counts = {}
                number_labeled += 1
                if number_labeled % 1000 == 0:
                    labeledcollection.message = "Labeling document #{}/{}".format(number_labeled, len(indices))
                    labeledcollection.save()
                for i in range(num_subdocs):
                    subdoc_toks = toks[i * toks_per : (i + 1) * toks_per]
                    content = [(t, [k for k, v in lexical_sets.items() if re.match(v, t, re.I)]) for t in subdoc_toks]
                    content = [(o, v[0]) for o, v in content if len(v) > 0]
                    subdoc_topic_counts = {}
                    for _, t in content:
                        topic_counts[t] = topic_counts.get(t, 0) + 1
                        subdoc_topic_counts[t] = subdoc_topic_counts.get(t, 0) + 1
                    subdoc = models.LabeledDocumentSection(
                        content=content,
                        labeleddocument=labeled_doc,
                        metadata={"topic_counts" : subdoc_topic_counts},
                        created_by=user,
                    )
                    subdoc.save()
                labeled_doc.metadata = {"topic_counts" : topic_counts}
                labeled_doc.save()
        elif labeledcollection.model:
            model = pickle.loads(labeledcollection.model.serialized) #LdaModel.load(output.model.disk_serialized.path)
            for j, doc in enumerate(labeledcollection.collection.documents()): #enumerate(models.Document.objects.only("id").filter(collection=labeledcollection.collection)):
                #if j not in indices:
                #    continue
                if "document_id" in doc:
                    labeled_doc = models.LabeledDocument(
                        document=doc["document"],
                        labeledcollection=labeledcollection,
                        created_by=user,
                    )
                else:
                    labeled_doc = models.LabeledDocument(
                        material_id=doc["material_id"],
                        labeledcollection=labeledcollection,
                        created_by=user,
                    )
                labeled_doc.save()
                number_labeled += 1
                if number_labeled % 1000 == 0:
                    labeledcollection.message = "Labeling document #{}/{}".format(number_labeled, len(indices))
                    labeledcollection.save()
                text = doc["text"]
                toks = [re.sub(labeledcollection.model.token_pattern_in, labeledcollection.model.token_pattern_out, t) for t in re.split(labeledcollection.model.split_pattern, text)]
                num_subdocs = round(0.5 + len(toks) / labeledcollection.model.max_context_size)
                toks_per = int(len(toks) / num_subdocs)
                labeled_toks = []
                topic_counts = {}
                for i in range(num_subdocs):
                    orig_subdoc_toks = toks[i * toks_per : (i + 1) * toks_per]
                    subdoc_toks = [t.lower() for t in orig_subdoc_toks] if labeledcollection.model.lowercase else orig_subdoc_toks
                    _, text_topics, _ = model.get_document_topics(model.id2word.doc2bow(subdoc_toks), per_word_topics=True)
                    word2topic = {model.id2word[wid] : -1 if len(topics) == 0 else topics[0] for wid, topics in text_topics}
                    #labeled_toks =
                    content = [(o, word2topic.get(t, -1)) for o, t in zip(orig_subdoc_toks, subdoc_toks)]
                    subdoc_topic_counts = {}
                    for _, t in content:
                        if t != -1:
                            topic_counts[t] = topic_counts.get(t, 0) + 1
                            subdoc_topic_counts[t] = subdoc_topic_counts.get(t, 0) + 1
                            
                    subdoc = models.LabeledDocumentSection(
                        content=content,
                        labeleddocument=labeled_doc,
                        metadata={"topic_counts" : subdoc_topic_counts},
                        created_by=user,
                    )
                    subdoc.save()
                labeled_doc.metadata = {"topic_counts" : topic_counts}
                labeled_doc.save()
        labeledcollection.state = labeledcollection.COMPLETE
    except Exception as e:
        labeledcollection.state = labeledcollection.ERROR
        labeledcollection.message = "{}".format(e)
        raise e
    labeledcollection.message = ""
    labeledcollection.save()
