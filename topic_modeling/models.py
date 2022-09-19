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
from primary_sources.models import Query
import pickle
import json
import random
import requests


logger = logging.getLogger(__name__)


class Lexicon(CdhModel):
    lexical_sets = models.TextField()

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
    max_context_size = models.IntegerField(default=5000, help_text="If a document has more tokens than this, it will be split up into sub-documents")
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

    @property
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

    @property
    @cdh_cache_method
    def topic_names(self, num_words=20):
        words = self.vega_words
        topic_names = {}
        for topic_id in range(self.topic_count):
            topic_words = [w for w in words if w["topic"] == str(topic_id + 1)]
            topic_names[topic_id + 1] = ", ".join([w["word"] for w in sorted(topic_words, key=lambda x : x["probability"], reverse=True)[:num_words]])
        return topic_names

    @cdh_action(detail=True, methods=["get"])
    def apply(self, collection):
        return {"status" : "success"}
