import logging
from rest_framework.serializers import ModelSerializer, BaseSerializer, HyperlinkedModelSerializer, HyperlinkedRelatedField
from rest_framework.serializers import ModelSerializer, HiddenField, CurrentUserDefault, HyperlinkedModelSerializer, HyperlinkedIdentityField, ReadOnlyField, FileField, CharField
from .models import PrimarySource, Query
from cdh.fields import VegaField, ActionOrInterfaceField, MonacoEditorField, TabularResultsField
from django.conf import settings
from .vega import PrimarySourceSchemaGraph
from cdh.serializers import CdhSerializer


logger = logging.getLogger(__name__)


class PrimarySourceSerializer(CdhSerializer):
    schema_file = FileField(write_only=True, allow_empty_file=True, allow_null=True, required=False)
    data_file = FileField(write_only=True, allow_empty_file=True, allow_null=True, required=False)
    annotations_file = FileField(write_only=True, allow_empty_file=True, allow_null=True, required=False)
    materials_file = FileField(write_only=True, allow_empty_file=True, allow_null=True, required=False)
    schema_url = ActionOrInterfaceField(
        VegaField(vega_class=PrimarySourceSchemaGraph, property_field="schema"),
        view_name="api:primarysource-schema",
    )    
    
    class Meta:
        model = PrimarySource
        fields = ["name", "schema_file", "data_file", "annotations_file", "materials_file", "created_by", "url", "schema_url", "id"]
        view_fields = ["schema_url"]
        edit_fields = ["name", "schema_file", "data_file", "annotations_file", "materials_file", "created_by", "url", "id"]
        create_fields = ["name", "schema_file", "data_file", "annotations_file", "materials_file", "created_by", "url", "id"]
        
    def create(self, validated_data):
        obj = PrimarySource.objects.create(name=validated_data["name"], created_by=validated_data["created_by"])
        obj.save(**validated_data)
        return obj


example_query = """
PREFIX cdh: <http://cdh.jhu.edu/materials/>
PREFIX so: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?title (SAMPLE(?u) as ?url) (SAMPLE(?p) as ?pub_date) (SAMPLE(?l) as ?lang)
WHERE {
  ?text so:creator ?author .
  ?author so:familyName ?last_name .
  ?author so:givenName ?first_name .
  ?text so:name ?title .
  ?text so:contentUrl ?u .
  ?text so:datePublished ?p .
  ?text so:inLanguage ?l .
  FILTER (?p > "1700-01-01"^^xsd:date && ?p < "1900-01-01"^^xsd:date)
} GROUP BY ?author ?title
"""

class QuerySerializer(CdhSerializer):
    primary_source = HyperlinkedRelatedField(view_name="api:primarysource-detail", queryset=PrimarySource.objects.all())
    sparql = MonacoEditorField(initial=example_query, language="sparql", property_field=None, allow_blank=True, required=False, endpoint="sparql", nested_parent_field="primary_source")
    perform_url = ActionOrInterfaceField(
        TabularResultsField(property_field="perform"),
        view_name="api:query-perform",
    )
    
    class Meta:
        model = Query
        fields = ["name", "primary_source", "sparql", "perform_url", "created_by", "url", "id"]
        view_fields = ["sparql", "perform_url", "id"]
        edit_fields = ["name", "primary_source", "sparql", "created_by", "url", "id"]
        create_fields = ["name", "primary_source", "sparql", "created_by", "url", "id"]
        
    def save(self, *argv, **argd):
        super(QuerySerializer, self).save(*argv, **argd)
