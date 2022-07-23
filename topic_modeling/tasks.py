import time
from cdh import settings
import zipfile
import random
import pickle
import json
import gzip
import logging
import re
import os
import tempfile
from datetime import datetime
from django.core.files.base import ContentFile
from . import models
from gensim.models import LdaModel
from gensim.corpora import Dictionary
from jsonpath import JSONPath
from spacy.lang import en
from gensim.models.callbacks import Metric

if settings.USE_CELERY:
    from celery import shared_task
else:
    def shared_task(func):
        return func

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
    has_temporality = False
    has_spatiality = False
    try:
        if fname.endswith("zip"):
            prepended_time = False
            with zipfile.ZipFile(fname) as zfd:
                if all([re.match(r"^\d+\_.*$", n) for n in zfd.namelist()]):
                    prepended_time = True
                    logging.info("Will extract time from each file name")
            with zipfile.ZipFile(fname) as zfd:
                for name in zfd.namelist():                    
                    with zfd.open(name) as ifd:
                        text = ifd.read().decode("utf-8")                        
                        if name.endswith("txt"):
                            year, title = re.match(r"^(?:(\d+)\_)?(.*)\.+txt", name).groups()
                            metadata = {}
                            docobj = models.Document(
                                title=title,                                
                                text=text,
                                collection=collection,
                                metadata=metadata,
                            )
                            if year:
                                docobj.year = year
                                has_temporality = True
                            docobj.longitude = (random.random() * 360.0) - 180.0
                            docobj.latitude = (random.random() * 180.0) - 90.0
                            docobj.save()
                        elif name.endswith("tei"):
                            pass
        elif fname.endswith("json"):
            # assume this is already in the right format
            with open(fname, "rt") as ifd:
                for line in ifd:
                    j = json.loads(line)
                    docobj = models.Document(
                        title=j.get("title", "Unknown")[0:1000],
                        content=doc,
                        collection=collection,
                    )
                    docobj.save()
                    #ofd.write(json.dumps(j) + "\n")
        elif fname.endswith("json.gz"):
            # assume this is already in the right format
            with gzip.open(fname, "rt") as ifd:
                for i, line in enumerate(ifd):
                    j = json.loads(line)
                    temporal = temporal_field.parse(j)
                    spatial = spatial_field.parse(j)
                    if len(temporal) > 0:
                        temporal = datetime.fromtimestamp(float(temporal[0]) / 1000)
                    if len(spatial) > 0:
                        spatial = spatial[0]
                    if temporal:
                        has_temporality = True
                    if spatial:
                        has_spatiality = True
                    title = title_field.parse(j)
                    author = author_field.parse(j)
                    text = text_field.parse(j)
                    lang = lang_field.parse(j)
                    if i % 1000 == 0:
                        collection.message = "{} document processed".format(i)
                        collection.save()
                    docobj = models.Document(
                        title=title[0] if len(title) > 0 else "",
                        text=text[0] if len(text) > 0 else "",
                        language = lang[0][:2] if len(lang) > 0 else "",
                        temporal=temporal,
                        spatial=spatial,
                        author=author[0] if len(author) > 0 else "",
                        collection=collection,
                    )                    
                    docobj.save()                    
        else:
            raise Exception("Unknown file type for '{}'".format(fname))
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
def train_model(topic_model_id):
    time.sleep(2)
    topic_model = models.TopicModel.objects.get(id=topic_model_id)
    topic_model.message = "Preparing training data"
    topic_model.save()
    collection = topic_model.collection
    random.seed(topic_model.random_seed)
    try:
        print("Querying documents")
        qs = models.Document.objects.filter(collection=collection).only("id")
        print("Making indices")        
        indices = list(range(qs.count()))
        print("Shuffling indices")
        random.shuffle(indices)
        print("Selecting indices")
        indices = set(indices[:topic_model.maximum_documents])
        print("Iterating documents")
        docs = []
        for i, doc in enumerate(qs): #enumerate(models.Document.objects.filter(collection=collection)):
            if i in indices:
                text = doc.text.lower() if topic_model.lowercase else doc.text
                toks = [re.sub(topic_model.token_pattern_in, topic_model.token_pattern_out, t) for t in re.split(topic_model.split_pattern, text) if t.lower() not in en.stop_words.STOP_WORDS]
                num_subdocs = round(0.5 + len(toks) / topic_model.max_context_size)
                toks_per = int(len(toks) / num_subdocs)
                for i in range(num_subdocs):
                    docs.append(toks[i * toks_per : (i + 1) * toks_per])                

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
def apply_model(labeledcollection_id):
    time.sleep(2)
    labeledcollection = models.LabeledCollection.objects.get(id=labeledcollection_id)
    labeledcollection.message = "Preparing to label documents"
    labeledcollection.save()
    try:
        print("Querying documents")
        qs = models.Document.objects.filter(collection=labeledcollection.collection).only("id")
        print("Making indices")        
        indices = list(range(qs.count()))
        print("Shuffling indices")
        random.shuffle(indices)
        print("Selecting indices")
        indices = set(indices[:labeledcollection.maximum_documents])
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
                    )
                    subdoc.save()
                labeled_doc.metadata = {"topic_counts" : topic_counts}
                labeled_doc.save()
        elif labeledcollection.model:
            model = pickle.loads(labeledcollection.model.serialized.tobytes()) #LdaModel.load(output.model.disk_serialized.path)
            for j, doc in enumerate(models.Document.objects.only("id").filter(collection=labeledcollection.collection)):
                if j not in indices:
                    continue
                labeled_doc = models.LabeledDocument(
                    document=doc,
                    labeledcollection=labeledcollection,
                )
                labeled_doc.save()
                number_labeled += 1
                if number_labeled % 1000 == 0:
                    labeledcollection.message = "Labeling document #{}/{}".format(number_labeled, len(indices))
                    labeledcollection.save()
                text = doc.text
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
