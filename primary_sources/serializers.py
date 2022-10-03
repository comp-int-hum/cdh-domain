import logging

from rest_framework.serializers import ModelSerializer, HiddenField, CurrentUserDefault, HyperlinkedModelSerializer, HyperlinkedIdentityField, ReadOnlyField, FileField, CharField, HyperlinkedRelatedField, JSONField
from .models import PrimarySource, Query, Annotation
from cdh.fields import VegaField, ActionOrInterfaceField, SparqlEditorField, TabularResultsField, AnnotationSourceField
from django.conf import settings
from .vega import PrimarySourceDomainGraph, PrimarySourceDataGraph
from cdh.serializers import CdhSerializer


logger = logging.getLogger(__name__)


class AnnotationSerializer(CdhSerializer):
    query = HyperlinkedRelatedField(view_name="api:query-detail", queryset=Query.objects.all())
    
    class Meta:
        model = Annotation
        fields = ["name", "query", "app_label", "model_class", "object_id", "created_by", "url", "id"]
        view_fields = ["id"]
        edit_fields = ["name", "url", "id"]
        create_fields = ["name", "query", "app_label", "model_class", "object_id", "created_by", "url", "id"]
        
    def save(self, *argv, **argd):
        super(AnnotationSerializer, self).save(*argv, **argd)


class PrimarySourceSerializer(CdhSerializer):
    domain_file = FileField(write_only=True, allow_empty_file=True, allow_null=True, required=False)
    data_file = FileField(write_only=True, allow_empty_file=True, allow_null=True, required=False)
    materials_file = FileField(write_only=True, allow_empty_file=True, allow_null=True, required=False)
    domain_url = ActionOrInterfaceField(
        VegaField(vega_class=PrimarySourceDomainGraph, property_field="domain"),
        view_name="api:primarysource-domain",
        title="Domain"
    )
    data_url = ActionOrInterfaceField(
        VegaField(vega_class=PrimarySourceDataGraph, property_field="data"),
        view_name="api:primarysource-data",
        title="Data"
    )
    #annotations = AnnotationSerializer()
    #ActionOrInterfaceField(
    #    #VegaField(vega_class=PrimarySourceDomainGraph, property_field="annotations"),
    #    view_name="api:primarysource-annotations",
    #    title="Annotations"
    #)
    
    class Meta:
        model = PrimarySource
        fields = ["name", "domain_file", "domain_url", "data_url", "data_file", "materials_file", "created_by", "url", "id"]
        view_fields = ["domain_url", "data_url"]
        edit_fields = ["name", "domain_file", "data_file", "materials_file", "created_by", "url", "id"]
        create_fields = ["name", "domain_file", "data_file", "materials_file", "created_by", "url", "id"]
        tab_view = True
        
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

example_query = """
PREFIX cdh: <http://cdh.jhu.edu/materials/>
PREFIX so: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?url WHERE {
  ?doc so:contentUrl ?url .
}
"""


class QuerySerializer(CdhSerializer):
    primarysource = HyperlinkedRelatedField(view_name="api:primarysource-detail", queryset=PrimarySource.objects.all())
    sparql = SparqlEditorField(
        initial=example_query,
        language="sparql",
        property_field=None,
        allow_blank=True,
        required=False,
        endpoint="sparql",
        nested_parent_field="primary_source"
    )
    perform_url = ActionOrInterfaceField(
        TabularResultsField(
            property_field="perform",
            column_names_path="head.vars",
            lookup_path="head.vars",
            rows_path="results.bindings",
            value_format="{0[value]}",
        ),
        view_name="api:query-perform",
    )
    
    class Meta:
        model = Query
        fields = ["name", "primarysource", "sparql", "perform_url", "created_by", "url", "id"]
        view_fields = ["sparql", "perform_url", "id"]
        edit_fields = ["name", "primarysource", "sparql", "created_by", "url", "id"]
        create_fields = ["name", "primarysource", "sparql", "created_by", "url", "id"]
        
    def save(self, *argv, **argd):
        super(QuerySerializer, self).save(*argv, **argd)


        
