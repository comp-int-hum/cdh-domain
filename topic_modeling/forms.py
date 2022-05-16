from django.forms import ModelForm, inlineformset_factory, Textarea, modelform_factory
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

CollectionForm = modelform_factory(
    models.Collection,
    fields=("name", "disk_serialized", "state"),
)

OutputForm = modelform_factory(
    models.Output,
    fields=("name", "collection", "model", "lexicon", "state"),
)
