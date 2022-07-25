from django.forms import ModelForm, modelform_factory, FileField, CharField
from .models import Lexicon, TopicModel, Collection, LabeledCollection, Document, LabeledDocument
from cdh.widgets import VegaWidget, MonacoEditorWidget


class LexiconForm(ModelForm):
    def __init__(self, *args, **kwargs):
        prefix = "{}-{}-{}".format(
            Lexicon._meta.app_label,
            Lexicon._meta.model_name,
            kwargs["instance"].id if kwargs.get("instance", False) else "unbound"
        )
        super().__init__(*args, prefix=prefix, **{k : v for k, v in kwargs.items() if k != "prefix"})

    class Meta:
        model = Lexicon

        fields = ('lexical_sets', 'name')

        widgets = {
            'lexical_sets': MonacoEditorWidget(language="json", content_field="lexical_sets", default_value="""{
  "positive_words": ["happy", "glad"],
  "negative_words": ["awful", "sad.*"]
}
""")
        }

        
TopicModelForm = modelform_factory(
    TopicModel,
    exclude=["state", "task_id", "message"]
)


class CollectionCreateForm(ModelForm):
    upload = FileField(label="File")
    class Meta:
        model = Collection
        fields = ("upload", "name")
        
