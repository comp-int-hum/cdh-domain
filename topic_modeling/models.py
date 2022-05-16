from django.db import models
from django.urls import reverse
import os.path
from cdh.models import User, AsyncMixin

def default_lexicon():
    return {
        "some_positive_words_and_patterns" : ["happy", "joy.*"],
        "and_negative_ones" : ["sad", "depress.*"]
    }

class Lexicon(models.Model):
    name = models.CharField(max_length=200)
    lexical_sets = models.JSONField(default=default_lexicon)
    def get_absolute_url(self):
        return reverse("topic_modeling:lexicon_detail", args=(self.id,))
    def __str__(self):
        return self.name

class Collection(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    disk_serialized = models.FileField(null=True, upload_to="shared/topic_modeling/collections")
    disk_serialized_processed = models.FileField(null=True, upload_to="shared/topic_modeling/processed_collections")
    def get_absolute_url(self):
        return reverse("topic_modeling:collection_detail", args=(self.id,))
    def __str__(self):
        return self.name
    
class TopicModel(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    topic_count = models.IntegerField(default=50)
    lowercase = models.BooleanField(default=True)
    max_context_size = models.IntegerField(default=500)    
    chunk_size = models.IntegerField(default=2000)
    minimum_count = models.IntegerField(default=0)
    maximum_proportion = models.FloatField(default=1.0)
    passes = models.IntegerField(default=1)    
    update_every = models.IntegerField(default=1)
    alpha = models.CharField(default="symmetric", choices=[("symmetric", "Symmetric"), ("asymmetric", "Asymmetric")], max_length=20)
    eta = models.CharField(default="symmetric", choices=[("symmetric", "Symmetric"), ("asymmetric", "Asymmetric")], max_length=20)
    iterations = models.IntegerField(default=50)
    random_seed = models.IntegerField(default=0)
    split_pattern = models.CharField(max_length=200, default=r"\s+")
    token_pattern_in = models.CharField(max_length=200, default=r"(\S+)")
    token_pattern_out = models.CharField(max_length=200, default=r"\1")
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True)
    disk_serialized = models.FileField(null=True, upload_to="shared/topic_modeling/models")
    disk_serialized_state = models.FileField(null=True, upload_to="shared/topic_modeling/models")
    disk_serialized_param = models.FileField(null=True, upload_to="shared/topic_modeling/models")
    disk_serialized_dict = models.FileField(null=True, upload_to="shared/topic_modeling/models")
    def get_absolute_url(self):
        return reverse("topic_modeling:topic_model_detail", args=(self.id,))
    def __str__(self):
        return self.name

class Output(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True)
    model = models.ForeignKey(TopicModel, on_delete=models.SET_NULL, null=True, blank=True)
    lexicon = models.ForeignKey(Lexicon, on_delete=models.SET_NULL, null=True, blank=True)
    results = models.JSONField(null=True)
    disk_serialized = models.FileField(null=True, upload_to="shared/topic_modeling/outputs")
    def get_absolute_url(self):
        return reverse("topic_modeling:output_detail", args=(self.id,))    
    def __str__(self):
        return self.name
