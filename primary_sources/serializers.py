import logging

from rest_framework.serializers import ModelSerializer, HiddenField, CurrentUserDefault, HyperlinkedModelSerializer, HyperlinkedIdentityField, ReadOnlyField, FileField, CharField, HyperlinkedRelatedField, JSONField, SerializerMethodField, Serializer
from .models import PrimarySource, Query, Annotation
from cdh.fields import VegaField, ActionOrInterfaceField, SparqlEditorField, TabularResultsField, AnnotationSourceField, AnnotationsField
from django.conf import settings
from .vega import PrimarySourceDomainGraph, PrimarySourceDataGraph, AnnotationGraph
from topic_modeling.vega import SpatialDistribution, TemporalEvolution
from cdh.serializers import CdhSerializer


logger = logging.getLogger(__name__)


class AnnotationSerializer(CdhSerializer):
    query = HyperlinkedRelatedField(view_name="api:query-detail", queryset=Query.objects.all())
    # data = ActionOrInterfaceField(
    #     VegaField(vega_class=AnnotationGraph, property_field="data"),
    #     view_name="api:annotation-data",
    #     title=""
    # )
    temporal = VegaField(
        vega_class=TemporalEvolution, #SpatialDistribution,
        property_field="data",
        allow_null=True,
        #required=False,
        read_only=True,
        #write_only=True,
        title="Temporal evolution"
    )
    spatial = VegaField(
        vega_class=SpatialDistribution,
        property_field="data",
        allow_null=True,
        #required=False,
        read_only=True,
        #write_only=True,
        title="Spatial distribution"
    )
    
    class Meta:
        model = Annotation
        fields = ["temporal", "spatial", "name", "query", "app_label", "model_class", "object_id", "created_by", "url", "id"]
        view_fields = ["temporal", "spatial", "id"]
        edit_fields = ["name", "url", "id"]
        create_fields = ["name", "query", "app_label", "model_class", "object_id", "created_by", "url", "id"]
        tab_view = True
        
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
        VegaField(vega_class=PrimarySourceDataGraph, property_field="data", property_field_args={"limit" : 10}),
        view_name="api:primarysource-data",
        title="Data"
    )
    
    class Meta:
        model = PrimarySource
        fields = ["name", "domain_file", "domain_url", "data_url", "data_file", "materials_file", "created_by", "url", "id"]        
        view_fields = ["domain_url"] #, "data_url"]
        edit_fields = ["name", "domain_file", "data_file", "materials_file", "created_by", "url", "id"]
        create_fields = ["name", "domain_file", "data_file", "materials_file", "created_by", "url", "id"]
        tab_view = True
        
    def create(self, validated_data):
        logging.info("%s", validated_data)
        obj = PrimarySource(name=validated_data["name"], created_by=validated_data["created_by"])
        obj.save(**validated_data)
        return obj


example_query = """
PREFIX cdh: <http://cdh.jhu.edu/>
PREFIX so: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?title (SAMPLE(?m) as ?mid) (SAMPLE(?p) as ?pub_date) (SAMPLE(?l) as ?lang)
WHERE {
  ?text so:creator ?author .
  ?author so:familyName ?last_name .
  ?author so:givenName ?first_name .
  ?text so:name ?title .
  ?text cdh:materialId ?m .
  ?text so:datePublished ?p .
  ?text so:inLanguage ?l .
  FILTER (?p > "1700-01-01"^^xsd:date && ?p < "1900-01-01"^^xsd:date)
} GROUP BY ?author ?title
"""

example_query = """
PREFIX cdh: <http://cdh.jhu.edu/materials/>
PREFIX so: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?mid WHERE {
  ?doc cdh:materialId ?mid .
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
            property_field_args={"limit" : 10},
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


class MaterialSerializer(Serializer):
    
    def __init__(self, *argv, **argd):
        
        # for field in self.Meta.model._meta.fields:
        #     if isinstance(field, ForeignKey):
        #         self.fields[field.name] = HyperlinkedRelatedField(
        #             view_name="api:{}-detail".format(field.related_model._meta.model_name),
        #             queryset=field.related_model.objects.all()
        #         )            
        retval = super(Serializer, self).__init__(*argv, **argd)
        # self.fields["url"] = HyperlinkedIdentityField(
        #     view_name="api:{}-detail".format(self.Meta.model._meta.model_name),
        #     lookup_field="id",
        #     lookup_url_kwarg="pk"
        # )
        # self.fields["created_by"] = HiddenField(
        #     default=CurrentUserDefault()
        # )
        return retval
