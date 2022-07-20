from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.contrib.gis.db import models
from django.urls import reverse
from cdh.models import BaseModel, User, AsyncMixin, MetadataMixin
import pickle


def default_lexicon():
    return {
        "some_positive_words_and_patterns" : ["happy", "joy.*"],
        "and_negative_ones" : ["sad", "depress.*"]
    }


class Lexicon(models.Model):
    name = models.CharField(max_length=200)
    #description = MarkdownField(blank=True, rendered_field="rendered_description", validator=VALIDATOR_STANDARD)
    #rendered_description = RenderedMarkdownField(null=True)
    lexical_sets = models.TextField(default="")
    def get_absolute_url(self):
        return reverse("topic_modeling:lexicon_detail", args=(self.id,))
    def __str__(self):
        return self.name


class Collection(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    #description = MarkdownField(blank=True, rendered_field="rendered_descriptoin", validator=VALIDATOR_STANDARD)
    #rendered_description = RenderedMarkdownField(null=True)
    has_spatiality = models.BooleanField(default=False)
    has_temporality = models.BooleanField(default=False)
    def get_absolute_url(self):
        return reverse("topic_modeling:collection_detail", args=(self.id,))
    def __str__(self):
        return self.name


class Document(MetadataMixin, models.Model):
    title = models.CharField(max_length=10000)
    text = models.TextField()
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=False)
    temporal = models.CharField(max_length=10000, null=True)
    spatial = models.CharField(max_length=10000, null=True)
    author = models.CharField(max_length=10000, null=True)
    year = models.IntegerField(null=True)
    datetime = models.DateTimeField(null=True)
    longitude = models.FloatField(null=True)
    latitude = models.FloatField(null=True)
    def get_absolute_url(self):
        return reverse("topic_modeling:document_detail", args=(self.id,))
    def __str__(self):
        return self.title


class TopicModel(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    #description = MarkdownField(blank=True, rendered_field="rendered_descriptoin", validator=VALIDATOR_STANDARD)
    #rendered_description = RenderedMarkdownField(null=True)    
    topic_count = models.IntegerField(default=10)
    lowercase = models.BooleanField(default=True)
    max_context_size = models.IntegerField(default=1000) #, help_text="Over what maximum distance (in words) should two words be considered 'co-occurring'?")
    chunk_size = models.IntegerField(default=2000)
    maximum_vocabulary = models.IntegerField(default=5000)
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
    maximum_documents = models.IntegerField(default=30000)
    def get_absolute_url(self):
        return reverse("topic_modeling:topicmodel_detail", args=(self.id,))
    @property
    def vega_words(self):
        try:
            model = pickle.loads(self.serialized.tobytes())
        except:
            return []
        words = sum([[{"word" : w, "probability" : float(p), "topic" : str(i + 1)} for w, p in model.show_topic(i, 50)] for i in range(model.num_topics)], [])
        return words
    #@property
    #def words(self):
    #    return self.vega[0]
    def __str__(self):
        return self.name


class LabeledCollection(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, null=True)
    model = models.ForeignKey(TopicModel, on_delete=models.CASCADE, null=True, blank=True)
    lexicon = models.ForeignKey(Lexicon, on_delete=models.CASCADE, null=True, blank=True)    
    def get_absolute_url(self):
        return reverse("topic_modeling:labeledcollection_detail", args=(self.id,))
    def __str__(self):
        return self.name
    def clean(self):
        if (self.model is None and self.lexicon is None) or (self.model is not None and self.lexicon is not None):
            raise ValidationError({NON_FIELD_ERRORS : "Exactly one of 'model' and 'lexicon' must be specified."})
        super(LabeledCollection, self).clean()
    @property
    def vega_spatial(self):
        model = pickle.loads(self.model.serialized.tobytes())    
        topics = dict([(tid, model.show_topic(tid)) for tid in range(self.model.topic_count)])
        coordinates = []
        for ld in LabeledDocument.objects.filter(labeled_collection=self):
            counts = {int(k) : v for k, v in ld.metadata["topic_counts"].items()}
            total = sum(counts.values())
            for t, v in counts.items():
                coordinates.append(
                    {
                        "topic" : t,
                        "weight" : v / total,
                        "latitude" : ld.document.latitude,
                        "longitude" : ld.document.longitude,
                    }
                )
        return coordinates
    @property
    def vega_temporal(self):
        model = pickle.loads(self.model.serialized.tobytes())
        topics = dict([(tid, model.show_topic(tid)) for tid in range(self.model.topic_count)])
        min_time, max_time = None, None        
        vals = []
        for ld in LabeledDocument.objects.filter(labeled_collection=self):
            time = ld.document.year
            min_time = time if min_time == None else min(min_time, time)
            max_time = time if max_time == None else max(max_time, time)
            vals.append((time, {int(k) : v for k, v in ld.metadata["topic_counts"].items()}))
        duration = 10
        minimum = min_time #1550

        all_years = set()
        all_labels = set()
        buckets = {}
        years = {}
        year_totals = {}
        for year, counts in vals:
            year = year - (year % duration)
            #if year < 1550:
            #    continue
            all_years.add(year)
            buckets[year] = buckets.get(year, 0) + 1
            for k, v in counts.items():
                label = ", ".join([w for w, _ in topics[k][0:10]])
                all_labels.add(label)
                years[year] = years.get(year, {})
                years[year][label] = years[year].get(label, 0.0) + v
                year_totals[year] = year_totals.get(year, 0.0) + v

        for label in all_labels:
            for year in all_years:
                if label not in years[year]:
                    print(year, label)
                years[year][label] = years[year].get(label, 0.0)

        data = sum(
            [
                [
                    {
                        "label" : label,
                        "value" : value / year_totals[year],
                        "year" : year
                    } for label, value in labels.items()] for year, labels in years.items()
            ],
            []
        )
        return data
        

class LabeledDocument(MetadataMixin, models.Model):
    labeled_collection = models.ForeignKey(LabeledCollection, on_delete=models.CASCADE, null=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True)
    def get_absolute_url(self):
        return reverse("topic_modeling:labeleddocument_detail", args=(self.id,))
    def __str__(self):
        return self.document.title


class LabeledDocumentSection(MetadataMixin, models.Model):
    labeled_document = models.ForeignKey(LabeledDocument, on_delete=models.CASCADE, null=True)
    content = models.JSONField(null=dict)
    def get_absolute_url(self):
        return reverse("topic_modeling:labeleddocumentsection_detail", args=(self.id,))
    def __str__(self):
        return "{}-{}".format(self.labeled_document.title, self.id)
    

class TemporalEvolution(models.Model):
    labeled_collection = models.ForeignKey(LabeledCollection, on_delete=models.CASCADE, null=True)
    content = models.JSONField(null=dict)
    def get_absolute_url(self):
        return reverse("topic_modeling:temporalevolution_detail", args=(self.id,))
    def __str__(self):
        return "{}-{}".format(self.labeled_collection.title)


class SpatialDistribution(models.Model):
    labeled_collection = models.ForeignKey(LabeledCollection, on_delete=models.CASCADE, null=True)
    content = models.JSONField(null=dict)
    def get_absolute_url(self):
        return reverse("topic_modeling:spatialevolution_detail", args=(self.id,))
    def __str__(self):
        return "{}-{}".format(self.labeled_collection.title)
