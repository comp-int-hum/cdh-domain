from markdownfield.widgets import MDEWidget, MDEAdminWidget
from django.forms import ModelForm, inlineformset_factory, Textarea, modelform_factory, FileField
from . import models
from cdh.models import User

#TopicModelForm = modelform_factory(
#    models.TopicModel,
    #fields=("name", "collection", "topic_count", "max_context_size", "lowercase", "split_pattern", "token_pattern_in", "token_pattern_out"),
#)

LexiconForm = modelform_factory(
    models.Lexicon,
    fields=("name", "lexical_sets"),
)


class CollectionForm(ModelForm):
    upload = FileField(label="File")
    class Meta:
        model = models.Collection
        fields = ("upload", "name", "description")
        widgets={
            "description" : MDEWidget,
        }


LabeledCollectionForm = modelform_factory(
    models.LabeledCollection,
    fields=("name", "collection", "model", "lexicon"),
)
