from django.forms import ModelForm, inlineformset_factory, Textarea, modelform_factory
from . import models
from cdh.models import User

# CollectionFormSet = inlineformset_factory(
#     User,
#     models.Collection,
#     fields=("name", "data"),
#     extra=1,
#     widgets={
#         "name" : Textarea(attrs={"cols" : 30, "rows" : 1}),
#     },
# )

TopicModelForm = modelform_factory(
    models.TopicModel,
    fields=("name", "topic_count", "max_context_size", "lowercase", "split_pattern", "token_pattern_in", "token_pattern_out"),
)

LexiconForm = modelform_factory(
    models.Lexicon,
    fields=("name",),
)

CollectionForm = modelform_factory(
    models.Collection,
    fields=("name", "data"),
)

OutputForm = modelform_factory(
    models.Output,
    fields=("name", "collection", "model", "lexicon"),
)
