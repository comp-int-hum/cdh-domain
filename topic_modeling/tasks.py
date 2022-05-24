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
if settings.USE_CELERY:
    from celery import shared_task
else:
    def shared_task(func):
        return func


# This needs to be modular
@shared_task
def extract_documents(collection_id, fname):
    collection = models.Collection.objects.get(id=collection_id)
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
                            year, title = re.match(r"^(?:(\d+)?\_)(.*)\.+txt", name).groups()
                            metadata = {}
                            
                            if year:
                                metadata["year"] = int(year)
                            docobj = models.Document(
                                title=title,                                
                                text=text,
                                collection=collection,
                                metadata=metadata,
                            )                            
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
        elif re.endswith("json.gz"):
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
        else:
            raise Exception("Unknown file type for '{}'".format(fname))
        collection.state = collection.COMPLETE
    except Exception as e:
        collection.state = collection.ERROR
        collection.message = str(e)        
        raise e
    finally:
        os.remove(fname)
    collection.save()


@shared_task
def train_model(topic_model_id):
    topic_model = models.TopicModel.objects.get(id=topic_model_id)
    collection = topic_model.collection
    random.seed(topic_model.random_seed)
    try:
        qs = models.Document.objects.filter(collection=collection)
        indices = list(range(qs.count()))
        random.shuffle(indices)
        indices = set(indices[:topic_model.maximum_documents])
        docs = []
        for i, doc in enumerate(qs): #enumerate(models.Document.objects.filter(collection=collection)):
            print(doc.title)
            if i in indices:
                text = doc.text.lower() if topic_model.lowercase else doc.text
                toks = [re.sub(topic_model.token_pattern_in, topic_model.token_pattern_out, t) for t in re.split(topic_model.split_pattern, text)]
                num_subdocs = round(0.5 + len(toks) / topic_model.max_context_size)
                toks_per = int(len(toks) / num_subdocs)
                for i in range(num_subdocs):
                    docs.append(toks[i * toks_per : (i + 1) * toks_per])                

        dictionary = Dictionary(docs)
        dictionary.filter_extremes(no_below=topic_model.minimum_occurrence, no_above=topic_model.maximum_proportion, keep_n=topic_model.maximum_vocabulary)
        corpus = [dictionary.doc2bow(doc) for doc in docs]
        model = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=topic_model.topic_count,
            alpha="auto",
            eta="auto",
            iterations=topic_model.iterations,
            passes=topic_model.passes,
            random_state=topic_model.random_seed,
            eval_every=None
        )
        topic_model.state = topic_model.COMPLETE
        topic_model.serialized = pickle.dumps(model)
    except Exception as e:
        topic_model.state = topic_model.ERROR
        topic_model.message = "{}".format(e)
        raise e
    topic_model.save()


@shared_task
def apply_model(labeled_collection_id):
    #output = models.Output.objects.get(id=output_id)
    #output.disk_serialized.save("{}".format(output.id), ContentFile("placeholder"))
    labeled_collection = models.LabeledCollection.objects.get(id=labeled_collection_id)
    try:
        if labeled_collection.lexicon:
            cache = {}
            lexical_sets = {name : "^({})$".format("|".join(terms)) for name, terms in output.lexicon.lexical_sets.items()}
            with gzip.open(output.collection.disk_serialized_processed.path, "rt") as ifd:
                for line in ifd:
                    j = json.loads(line)
                    text = j["text"]
                    toks = re.sub(r"\s+", " ", text).split()
                    labeled_toks = []
                    for tok in toks:
                        if tok not in cache:
                            cache[tok] = ""
                            for name, pattern in lexical_sets.items():
                                if re.match(pattern, tok, re.I):
                                    cache[tok] = name
                                    break
                        labeled_toks.append((tok, cache[tok]))
                    ofd.write(json.dumps(labeled_toks) + "\n")                            
        elif labeled_collection.model:
            model = pickle.loads(labeled_collection.model.serialized.tobytes()) #LdaModel.load(output.model.disk_serialized.path)
            for j, doc in enumerate(models.Document.objects.filter(collection=labeled_collection.collection)):
                text = doc.text
                print(j, doc.title)
                toks = [re.sub(labeled_collection.model.token_pattern_in, labeled_collection.model.token_pattern_out, t) for t in re.split(labeled_collection.model.split_pattern, text)]
                num_subdocs = round(0.5 + len(toks) / labeled_collection.model.max_context_size)
                toks_per = int(len(toks) / num_subdocs)
                labeled_toks = []
                for i in range(num_subdocs):
                    orig_subdoc_toks = toks[i * toks_per : (i + 1) * toks_per]
                    subdoc_toks = [t.lower() for t in orig_subdoc_toks] if labeled_collection.model.lowercase else orig_subdoc_toks
                    _, text_topics, _ = model.get_document_topics(model.id2word.doc2bow(subdoc_toks), per_word_topics=True)
                    word2topic = {model.id2word[wid] : -1 if len(topics) == 0 else topics[0] for wid, topics in text_topics}
                    labeled_toks += [(o, word2topic.get(t, -1)) for o, t in zip(orig_subdoc_toks, subdoc_toks)]
                #text = text.lower() if labeled_collection.model.lowercase else text
                #toks = [re.sub(labeled_collection.model.token_pattern_in, labeled_collection.model.token_pattern_out, t) for t in re.split(labeled_collection.model.split_pattern, text)]
                
                #_, text_topics, _ = model.get_document_topics(model.id2word.doc2bow(toks), per_word_topics=True)
                #word2topic = {model.id2word[wid] : -1 if len(topics) == 0 else topics[0] for wid, topics in text_topics}
                #labeled_toks = [(otok, word2topic.get(tok, "")) for tok, otok in zip(toks, otoks)]
                print(len(labeled_toks))
                labeled_doc = models.LabeledDocument(
                    document=doc,
                    labeled_collection=labeled_collection,
                    content=json.dumps(labeled_toks).encode(),
                )
                labeled_doc.save()
        labeled_collection.state = labeled_collection.COMPLETE
    except Exception as e:
        labeled_collection.state = labeled_collection.ERROR
        labeled_collection.message = "{}".format(e)
        raise e        
    labeled_collection.save()
