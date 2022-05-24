from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db import models
from django.urls import reverse
from cdh.models import User, AsyncMixin, MetadataMixin
from markdownfield.models import MarkdownField, RenderedMarkdownField
from markdownfield.validators import VALIDATOR_STANDARD


def default_lexicon():
    return {
        "some_positive_words_and_patterns" : ["happy", "joy.*"],
        "and_negative_ones" : ["sad", "depress.*"]
    }


class Lexicon(models.Model):
    name = models.CharField(max_length=200)
    description = MarkdownField(blank=True, rendered_field="rendered_descriptoin", validator=VALIDATOR_STANDARD)
    rendered_description = RenderedMarkdownField(null=True)
    lexical_sets = models.JSONField(default=default_lexicon)
    def get_absolute_url(self):
        return reverse("topic_modeling:lexicon_detail", args=(self.id,))
    def __str__(self):
        return self.name


class Collection(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    description = MarkdownField(blank=True, rendered_field="rendered_descriptoin", validator=VALIDATOR_STANDARD)
    rendered_description = RenderedMarkdownField(null=True)
    def get_absolute_url(self):
        return reverse("topic_modeling:collection_detail", args=(self.id,))
    def __str__(self):
        return self.name


class Document(MetadataMixin, models.Model):
    title = models.CharField(max_length=1000)
    text = models.TextField()
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=False)
    def get_absolute_url(self):
        return reverse("topic_modeling:document_detail", args=(self.id,))
    def __str__(self):
        return self.title


class TopicModel(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    description = MarkdownField(blank=True, rendered_field="rendered_descriptoin", validator=VALIDATOR_STANDARD)
    rendered_description = RenderedMarkdownField(null=True)    
    topic_count = models.IntegerField(default=20)
    lowercase = models.BooleanField(default=True)
    max_context_size = models.IntegerField(default=1000, help_text="Over what maximum distance (in words) should two words be considered 'co-occurring'?")
    chunk_size = models.IntegerField(default=2000)
    maximum_vocabulary = models.IntegerField(default=10000)
    minimum_occurrence = models.IntegerField(default=5)
    maximum_proportion = models.FloatField(default=0.5)
    passes = models.IntegerField(default=20)
    update_every = models.IntegerField(default=1)
    alpha = models.CharField(default="symmetric", choices=[("symmetric", "Symmetric"), ("asymmetric", "Asymmetric")], max_length=20)
    eta = models.CharField(default="symmetric", choices=[("symmetric", "Symmetric"), ("asymmetric", "Asymmetric")], max_length=20)
    iterations = models.IntegerField(default=40)
    random_seed = models.IntegerField(default=0)
    split_pattern = models.CharField(max_length=200, default=r"\s+")
    token_pattern_in = models.CharField(max_length=200, default=r"(\S+)")
    token_pattern_out = models.CharField(max_length=200, default=r"\1")
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    serialized = models.BinaryField(null=True)
    maximum_documents = models.IntegerField(default=1000)
    def get_absolute_url(self):
        return reverse("topic_modeling:topic_model_detail", args=(self.id,))
    def __str__(self):
        return self.name


class LabeledCollection(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True)
    model = models.ForeignKey(TopicModel, on_delete=models.CASCADE, null=True, blank=True)
    lexicon = models.ForeignKey(Lexicon, on_delete=models.CASCADE, null=True, blank=True)    
    def get_absolute_url(self):
        return reverse("topic_modeling:labeled_collection_detail", args=(self.id,))
    def __str__(self):
        return self.name
    def clean(self):
        if (self.model is None and self.lexicon is None) or (self.model is not None and self.lexicon is not None):
            raise ValidationError({NON_FIELD_ERRORS : "Exactly one of 'model' and 'lexicon' must be specified."})
        super(LabeledCollection, self).clean()


class LabeledDocument(models.Model):
    labeled_collection = models.ForeignKey(LabeledCollection, on_delete=models.CASCADE, null=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True)
    content = models.BinaryField(null=True)
    def get_absolute_url(self):
        return reverse("topic_modeling:labeled_document_detail", args=(self.id,))
    def __str__(self):
        return self.document.title
