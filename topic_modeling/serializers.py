import logging
from cdh.fields import VegaField, MonacoEditorField
from cdh.serializers import CdhSerializer
from cdh.widgets import VegaWidget
from primary_sources.models import Query
from .models import TopicModel, Lexicon
from .tasks import extract_documents, train_model, apply_model
from .vega import WordCloud


logger = logging.getLogger(__name__)


class TopicModelSerializer(CdhSerializer):
    topic_word_probabilities = VegaField(vega_class=WordCloud, property_field="topic_word_probabilities", required=False)

    class Meta:
        model = TopicModel
        fields = ["name", "query", "url", "created_by", "id", "topic_count", "lowercase", "max_context_size", "topic_word_probabilities"]
        view_fields = ["topic_word_probabilities", "id"]
        edit_fields = ["name", "id"]
        create_fields = ["name", "query", "created_by", "topic_count", "lowercase", "max_context_size", "url", "id"]
            #{
            #    "type" : "table",
            #    "title" : "Topic-Word Table",
            #    "property" : "topic_word_probabilities",
            #    "content" : "other",
            #}
        
    def update(self, instance, validated_data):
        return instance
        
    def create(self, validated_data):
        fields = [f.name for f in TopicModel._meta.fields]
        obj = TopicModel.objects.create(**{k : v for k, v in validated_data.items() if k in fields})
        train_model.delay(obj.id, **{k : v for k, v in validated_data.items() if isinstance(v, (str, int, float, list, tuple))})
        return obj

    def build_standard_field(self, field_name, model_field):
        field_class, kwargs = super(TopicModelSerializer, self).build_standard_field(field_name, model_field)
        if isinstance(model_field.default, (int, float, str)):
            kwargs["initial"] = model_field.default
        return (field_class, kwargs)


example_lexicon = """
{
  "some_positive_words_and_patterns" : [
    "happy",
    "joy.*"
  ],
  "and_negative_ones" : [
    "sad",
    "depress.*"
  ]
}
"""


class LexiconSerializer(CdhSerializer):
    lexical_sets = MonacoEditorField(language="json", initial=example_lexicon)
    class Meta:
        model = Lexicon
        fields = ["name", "lexical_sets", "url", "created_by", "id"]
        view_fields = ["lexical_sets", "id"]
        edit_fields = ["name", "lexical_sets", "id"]
        create_fields = ["name", "lexical_sets", "created_by", "url", "id"]
