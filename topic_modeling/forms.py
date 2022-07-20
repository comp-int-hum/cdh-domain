from django.forms import ModelForm, modelform_factory, FileField
from cdh import widgets
from .models import Lexicon, TopicModel, Collection, LabeledCollection, Document, LabeledDocument
from django.forms import FileField, JSONField, CharField
from cdh.widgets import VegaWidget
from .vega import TopicModelWordCloud

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
            'lexical_sets': widgets.MonacoEditorWidget(language="json", content_field="lexical_sets", default_value="""{
  "positive_items": ["happy", "glad"],
  "negative_items": ["awful", "sad*"]
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


class TopicModelWordCloudForm(ModelForm):
    topics = CharField(widget=VegaWidget(vega_class=TopicModelWordCloud), label="")

    def __init__(self, *argv, **argd):
        if argd["instance"]:
            argd["initial"]["topics"] = argd["instance"].vega
        super(TopicModelWordCloudForm, self).__init__(*argv, **argd)
        
    class Meta:        
        model = TopicModel
        fields = ('topics',)


class TopicModelWordTableForm(ModelForm):
    topics = CharField(widget=VegaWidget(vega_class=TopicModelWordCloud), label="")

    def __init__(self, *argv, **argd):
        if argd["instance"]:
            argd["initial"]["topics"] = argd["instance"].vega
        super(TopicModelWordTableForm, self).__init__(*argv, **argd)
        
    class Meta:        
        model = TopicModel
        fields = ('topics',)

        

class LabeledCollectionTemporalForm(ModelForm):
    topics = CharField(widget=VegaWidget(vega_class=TopicModelWordCloud), label="")

    def __init__(self, *argv, **argd):
        if argd["instance"]:
            argd["initial"]["topics"] = argd["instance"].vega
        super(LabeledCollectionTemporalForm, self).__init__(*argv, **argd)
        
    class Meta:        
        model = LabeledCollection
        fields = ('topics',)


class LabeledCollectionGeographicForm(ModelForm):
    topics = CharField(widget=VegaWidget(vega_class=TopicModelWordCloud), label="")

    def __init__(self, *argv, **argd):
        if argd["instance"]:
            argd["initial"]["topics"] = argd["instance"].vega
        super(LabeledCollectionGeographicForm, self).__init__(*argv, **argd)
        
    class Meta:        
        model = LabeledCollection
        fields = ('topics',)
        
