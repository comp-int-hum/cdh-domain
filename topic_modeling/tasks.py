from cdh import settings
import zipfile
import json
import gzip
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


@shared_task
def extract_documents(collection_id):
    collection = models.Collection.objects.get(id=collection_id)
    collection.disk_serialized_processed.save("{}".format(collection.id), ContentFile("placeholder"))
    fname = collection.disk_serialized.path
    try:
        with gzip.open(collection.disk_serialized_processed.path, "wt") as ofd:
            if fname.endswith("zip"):
                with zipfile.ZipFile(fname) as zfd:
                    for name in zfd.namelist():
                        with zfd.open(name) as ifd:
                            text = ifd.read().decode("utf-8")
                            if name.endswith("txt"):
                                ofd.write(json.dumps({"id" : name, "text" : text}) + "\n")
                            elif name.endswith("tei"):
                                pass
            elif fname.endswith("json"):
                # assume this is already in the right format
                with open(fname, "rt") as ifd:
                    for line in ifd:
                        j = json.loads(line)
                        ofd.write(json.dumps(j) + "\n")
            elif re.endswith("json.gz"):
                # assume this is already in the right format
                with open(fname, "rt") as ifd:
                    for line in ifd:
                        j = json.loads(line)
                        ofd.write(json.dumps(j) + "\n")
            else:
                raise Exception("Unknown file type for '{}'".format(fname))
        collection.state = collection.COMPLETE
    except Exception as e:
        collection.state = collection.ERROR
        collection.message = str(e)
        print(e)
        raise e
    collection.save()



@shared_task
def train_model(topic_model_id):
    topic_model = models.TopicModel.objects.get(id=topic_model_id)
    collection = topic_model.collection
    try:
        # doc_count
        # with gzip.open(collection.disk_serialized_processed.path, "rt") as ifd:
        #     for line in ifd:
        #         j = json.loads(line)
        #         text = j["text"].lower() if topic_model.lowercase else j["text"]
        #         toks = [re.sub(topic_model.token_pattern_in, topic_model.token_pattern_out, t) for t in re.split(topic_model.split_pattern, text)]
        #         num_subdocs = round(0.5 + len(toks) / topic_model.max_context_size)
        #         toks_per = int(len(toks) / num_subdocs)
        #         for i in range(num_subdocs):
        #             docs.append(toks[i * toks_per : (i + 1) * toks_per])        
        docs = []
        with gzip.open(collection.disk_serialized_processed.path, "rt") as ifd:
            for line in ifd:
                j = json.loads(line)
                text = j["text"].lower() if topic_model.lowercase else j["text"]
                toks = [re.sub(topic_model.token_pattern_in, topic_model.token_pattern_out, t) for t in re.split(topic_model.split_pattern, text)]
                num_subdocs = round(0.5 + len(toks) / topic_model.max_context_size)
                toks_per = int(len(toks) / num_subdocs)
                for i in range(num_subdocs):
                    docs.append(toks[i * toks_per : (i + 1) * toks_per])
        print(len(docs))
        dictionary = Dictionary(docs)
        dictionary.filter_extremes(no_below=topic_model.minimum_count, no_above=topic_model.maximum_proportion)
        print(len(dictionary))
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
        topic_model.disk_serialized.save("{}".format(topic_model.id), ContentFile("placeholder"))
        topic_model.disk_serialized_dict.save("{}.id2word".format(topic_model.id), ContentFile("placeholder"))
        topic_model.disk_serialized_param.save("{}.expElogbeta.npy".format(topic_model.id), ContentFile("placeholder"))
        topic_model.disk_serialized_state.save("{}.state".format(topic_model.id), ContentFile("placeholder"))
        model.save(topic_model.disk_serialized.path, separately=[])
        topic_model.state = topic_model.COMPLETE        
    except Exception as e:
        topic_model.state = topic_model.ERROR
        topic_model.message = "{}".format(e)
        print(e)
        raise e
    topic_model.save()


@shared_task
def apply_model(output_id):
    output = models.Output.objects.get(id=output_id)
    output.disk_serialized.save("{}".format(output.id), ContentFile("placeholder"))
    results = []
    with gzip.open(output.disk_serialized.path, "wt") as ofd:
        if output.lexicon:
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
        elif output.model:
            model = LdaModel.load(output.model.disk_serialized.path)
            with gzip.open(output.collection.disk_serialized_processed.path, "rt") as ifd:
                for line in ifd:
                    j = json.loads(line)
                    text = j["text"]
                    otoks = [re.sub(output.model.token_pattern_in, output.model.token_pattern_out, t) for t in re.split(output.model.split_pattern, text)]
                    text = j["text"].lower() if output.model.lowercase else j["text"]
                    toks = [re.sub(output.model.token_pattern_in, output.model.token_pattern_out, t) for t in re.split(output.model.split_pattern, text)]
                    _, text_topics, _ = model.get_document_topics(model.id2word.doc2bow(toks), per_word_topics=True)
                    word2topic = {model.id2word[wid] : -1 if len(topics) == 0 else topics[0] for wid, topics in text_topics}
                    labeled_toks = [(otok, word2topic.get(tok, "")) for tok, otok in zip(toks, otoks)]
                    ofd.write(json.dumps(labeled_toks) + "\n")
    output.results = results
    output.state = output.COMPLETE
    output.save()
