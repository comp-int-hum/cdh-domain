from cdh import settings
import json
import gzip
import re
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
    try:
        with gzip.open(collection.data.path, "rt") as ifd:
            for line in ifd:
                item = {"collection" : collection}
                for k, v in json.loads(line).items():
                    if k in ["title", "author", "text", "latitude", "longitude"]:
                        item[k] = v
                    elif k == "year":
                        item["date"] = datetime(v, 1, 1)
                doc = models.Document(**item)
                doc.save()
        collection.state = collection.COMPLETE
    except Exception as e:
        collection.state = collection.ERROR
        collection.message = "{}".format(e)
    collection.save()


@shared_task
def train_model(topic_model_id):
    topic_model = models.TopicModel.objects.get(id=topic_model_id)
    try:
        docs = []
        for document in models.Document.objects.filter(collection=topic_model.collection):
            text = document.text.lower() if topic_model.lowercase else document.text
            toks = [re.sub(topic_model.token_pattern_in, topic_model.token_pattern_out, t) for t in re.split(topic_model.split_pattern, text)]
            num_subdocs = round(0.5 + len(toks) / topic_model.max_context_size)
            toks_per = int(len(toks) / num_subdocs)
            for i in range(num_subdocs):
                docs.append(toks[i * toks_per : (i + 1) * toks_per])
        dictionary = Dictionary(docs)
        dictionary.filter_extremes(no_below=100, no_above=0.3)
        corpus = [dictionary.doc2bow(doc) for doc in docs]
        model = LdaModel(
            corpus=corpus,
            id2word=dictionary,
            num_topics=topic_model.topic_count,
            alpha="auto",
            eta="auto",
            iterations=10,
            passes=2,
            eval_every=None
        )
        topic_model.data.save("{}".format(topic_model.id), ContentFile("test"))
        model.save(topic_model.data.path)
        topic_model.state = topic_model.COMPLETE        
    except Exception as e:
        topic_model.state = topic_model.ERROR
        topic_model.message = "{}".format(e)
        print(e)
    topic_model.save()

