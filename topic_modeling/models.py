from django.db import models
from django.urls import reverse
import os.path
from cdh.models import User, AsyncMixin


class Lexicon(models.Model):
    name = models.CharField(max_length=200)
    def get_absolute_url(self):
        return reverse("topic_modeling:lexicon_detail", args=(self.id,))


class Collection(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    data = models.FileField(null=True, upload_to="collections")
    def get_absolute_url(self):
        return reverse("topic_modeling:collection_detail", args=(self.id,))

    
class Document(models.Model):
    title = models.TextField(null=True)
    author = models.TextField(null=True)
    text = models.TextField(null=True)
    date = models.DateTimeField(null=True)
    latitude = models.FloatField(null=True)
    longitude = models.FloatField(null=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True)
    def get_absolute_url(self):
        return reverse("topic_modeling:document", args=(self.id,))


class TopicModel(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    topic_count = models.IntegerField(default=50)
    max_context_size = models.IntegerField(default=3000)
    lowercase = models.BooleanField(default=True)
    split_pattern = models.CharField(max_length=200, default=r"\s+")
    token_pattern_in = models.CharField(max_length=200, default=r"(\S+)")
    token_pattern_out = models.CharField(max_length=200, default=r"\1")
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True)
    data = models.FileField(null=True, upload_to="models")    
    def get_absolute_url(self):
        return reverse("topic_modeling:topic_model_detail", args=(self.id,))


class Output(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)    
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True)
    model = models.ForeignKey(TopicModel, on_delete=models.SET_NULL, null=True)
    lexicon = models.ForeignKey(Lexicon, on_delete=models.SET_NULL, null=True)
    def get_absolute_url(self):
        return reverse("topic_modeling:output_detail", args=(self.id,))    

model_classes = [Lexicon, Collection, Document, TopicModel, Output]
