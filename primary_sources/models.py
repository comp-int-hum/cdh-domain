import json
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from cdh import settings
from cdh.models import CdhModel, User, AsyncMixin
from django.urls import path, reverse
import requests
from rdflib import Graph

schema_query = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX owl2: <http://www.w3.org/2006/12/owl2#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX schema: <https://schema.org/>
SELECT ?domain ?property ?range ?propertyType ?equivProperty ?equivDomain ?equivRange
WHERE {
  ?property rdfs:domain ?domain .
  ?property rdf:type ?propertyType .
  ?property rdfs:range ?range .
  ?domain rdf:type owl:Class .
  OPTIONAL {
    ?property owl2:equivalentProperty ?equivProperty .
    ?domain owl2:equivalentProperty ?equivDomain .
    ?range owl2:equivalentProperty ?equivRange .
  }
}
"""


class PrimarySource(CdhModel):
    name = models.CharField(max_length=1000)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("primary_sources:primarysource_detail", args=(self.id,))

    @property
    def schema(self):
        resp = requests.get(
            "http://{}:{}/{}_{}/get".format(settings.JENA_HOST, settings.JENA_PORT, self.id, "schema"),
            headers={"Accept" : "application/ld+json"},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        return json.loads(resp.content.decode("utf-8"))

    @property
    def vega_triples(self):
        value = self.schema
        entities, relationships, properties = [], [], []
        for triple in value["@graph"]:
            if triple.get("@type") == "owl:Class":
                entities.append(
                    {
                        "entity_label" : triple["@id"].split("/")[-1]
                    }
                )
            elif triple.get("@type") == "owl:ObjectProperty":                
                relationships.append(
                    {
                        "source_label" : triple["domain"].split("/")[-1],
                        "target_label" : triple["range"].split("/")[-1],
                        "relationship_label" : triple["@id"].split("/")[-1],
                    }
                )
            elif triple.get("@type") == "owl:DatatypeProperty":
                properties.append(
                    {
                        "entity_label" : triple["domain"].split("/")[-1],
                        "property_label" : triple["@id"].split("/")[-1],
                        #"property_type" : triple["range"].split(":")[-1],
                    }
                )
        return {"entities" : entities, "relationships" : relationships, "properties" : properties}

    @property
    def annotations(self):
        resp = requests.get(
            "http://{}:{}/{}_{}/get".format(settings.JENA_HOST, settings.JENA_PORT, self.id, "annotations"),
            headers={"Accept" : "application/ld+json"},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        return resp.content.decode("utf-8")
    
    @property
    def data(self):
        resp = requests.get(
            "http://{}:{}/{}_{}/get".format(settings.JENA_HOST, settings.JENA_PORT, self.id, "data"),
            headers={"Accept" : "application/ld+json"},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        return resp.content.decode("utf-8")
    
    def save(self, schema_fd=None, annotation_fd=None, data_fd=None, materials_fd=None):
        super(PrimarySource, self).save()
        if settings.USE_JENA:
            for graph_name, data_fd in [
                    ("schema", schema_fd),
                    ("annotation", annotation_fd),
                    ("data", data_fd)
            ]:                
                dbName = "{}_{}".format(self.id, graph_name)
                requests.post(
                    "http://{}:{}/$/datasets".format(settings.JENA_HOST, settings.JENA_PORT),
                    params={"dbName" : dbName, "dbType" : "tdb"},
                    auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
                )
                if data_fd != None:
                    resp = requests.put(
                        "http://{}:{}/{}/data".format(settings.JENA_HOST, settings.JENA_PORT, dbName),
                        headers={"default" : "", "Content-Type" : data_fd.content_type},
                        data=data_fd,
                        auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)                    
                    )

    
class Query(CdhModel):
    name = models.CharField(max_length=1000)
    sparql = models.TextField()
    dataset = models.ForeignKey(PrimarySource, on_delete=models.CASCADE, null=True)
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse("primary_sources:index", args=(self.id,))


@receiver(pre_delete, sender=PrimarySource, dispatch_uid="unique enough")
def remove_dataset(sender, instance, **kwargs):
    if settings.USE_JENA:
        for graph_name in ["schema", "data", "annotation"]:
            requests.delete(
                "http://{}:{}/$/datasets/{}_{}".format(settings.JENA_HOST, settings.JENA_PORT, instance.id, graph_name),
                auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
            )
    else:
        pass
