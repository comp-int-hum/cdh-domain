import logging
from rest_framework.serializers import CharField, BooleanField
from cdh.fields import VegaField, JsonEditorField, ActionOrInterfaceField, TabularResultsField, AnnotationField
from cdh.serializers import CdhSerializer
from cdh.widgets import VegaWidget
from primary_sources.models import Query
from .models import TopicModel, Lexicon
from .vega import WordCloud


logger = logging.getLogger(__name__)


class TopicModelSerializer(CdhSerializer):
    topic_word_probabilities = VegaField(
        vega_class=WordCloud,
        property_field="topic_word_probabilities",
        required=False,
        title="Word clouds"
    )
    topics_url = ActionOrInterfaceField(
        TabularResultsField(
            property_field="topics",
            column_names_path="column_names",
            row_names_path="row_names",
            column_label_path="column_label",
            row_label_path="row_label",
            rows_path="rows",
            value_format="{0[probability]:.03f}:{0[word]}",
        ),
        view_name="api:topicmodel-topics",
        title="Most-probable words by topic"
    )
    url_field = CharField(initial="url", write_only=True, default="url", required=False)
    text_field = CharField(initial="text", write_only=True, default="text", required=False)
    remove_stopwords = BooleanField(initial=True, write_only=True, default=True, required=False)
    apply_url = AnnotationField(model_field="apply", view_name="api:topicmodel-apply")
    
    class Meta:
        model = TopicModel
        fields = ["apply_url", "name", "query", "url", "created_by", "id", "topic_count", "lowercase", "maximum_documents", "max_context_size", "maximum_vocabulary", "minimum_occurrence", "maximum_proportion", "url_field", "text_field", "topic_word_probabilities", "topics_url", "remove_stopwords"]
        view_fields = ["apply_url", "topic_word_probabilities", "topics_url", "id"]
        #view_fields = ["apply_url", "topics_url", "id"]
        edit_fields = ["name", "id"]
        create_fields = ["name", "query", "created_by", "topic_count", "lowercase", "maximum_documents", "max_context_size", "url_field", "text_field", "remove_stopwords", "maximum_vocabulary", "minimum_occurrence", "maximum_proportion", "url", "id"]
        tab_view = True
        
    def update(self, instance, validated_data):
        return instance
        
    def create(self, validated_data):
        fields = [f.name for f in TopicModel._meta.fields]
        obj = TopicModel(**{k : v for k, v in validated_data.items() if k in fields})
        obj.save(url_field=validated_data["url_field"], text_field=validated_data["text_field"], remove_stopwords=validated_data["remove_stopwords"])
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
    lexical_sets = JsonEditorField(initial=example_lexicon, required=False, default=example_lexicon)
    apply_url = AnnotationField(model_field="apply", view_name="api:lexicon-apply")
    class Meta:
        model = Lexicon
        fields = ["name", "apply_url", "lexical_sets", "url", "created_by", "id"]
        view_fields = ["apply_url", "lexical_sets", "id"]
        edit_fields = ["name", "lexical_sets", "id"]
        create_fields = ["name", "lexical_sets", "created_by", "url", "id"]
