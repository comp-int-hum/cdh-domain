import json
import zipfile
import os.path
from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from cdh import settings
from cdh.models import CdhModel, User, AsyncMixin
from cdh.fields import SparqlField
from django.urls import path, reverse
import requests
from rdflib import Graph
from rdflib.namespace import SH, RDF, RDFS
import rdflib
from pairtree import PairtreeStorageFactory


if settings.USE_CELERY:
    from celery import shared_task
else:
    def shared_task(func):
        return func


class PrimarySource(AsyncMixin, CdhModel):

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
        schema = self.schema
        g = Graph()
        g.parse(data=json.dumps(schema), format="application/ld+json")        
        entities, relationships, properties = {}, {}, {}
            
        for shape, _, entity in g.triples((None, SH.targetClass, None)):
            entities[shape] = {
                "entity_label" : os.path.basename(entity)
            }

        for bnode, _, entity in g.triples((None, SH["class"], None)):
            relationships[bnode] = {
                "target_label" : os.path.basename(entity)
            }
            
        for shape, _, bnode in g.triples((None, SH.property, None)):
            if bnode not in relationships:
                properties[bnode] = {
                    "entity_label" : entities[shape]["entity_label"]
                }
            else:
                relationships[bnode]["source_label"] = entities[shape]["entity_label"]

        for bnode, _, path in g.triples((None, SH.path, None)):
            if bnode in properties:
                properties[bnode]["property_label"] = os.path.basename(path)
            else:
                relationships[bnode]["relationship_label"] = os.path.basename(path)
        return {"entities" : list(entities.values()), "relationships" : list(relationships.values()), "properties" : list(properties.values())}

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
        update = self.id and True
        retval = super(PrimarySource, self).save()                    
        for name, fd in [
                ("schema", schema_fd),
                ("annotation", annotation_fd),
                ("data", data_fd),
                ("materials", materials_fd)
        ]:
            if fd != None:
                with open(os.path.join(settings.TEMP_ROOT, "primarysource_{}_{}".format(self.id, name)), "wb") as ofd:
                    ofd.write(fd.read())
                with open(os.path.join(settings.TEMP_ROOT, "primarysource_{}_{}.meta".format(self.id, name)), "wt") as ofd:
                    ofd.write(fd.content_type)
        save_primarysource.delay(self.id, update)
        return retval
                    

class Query(CdhModel):
    sparql = SparqlField()
    primary_source = models.ForeignKey(PrimarySource, on_delete=models.CASCADE, null=False)
    def __str__(self):
        return self.name
    def get_absolute_url(self):
        return reverse("primary_sources:index", args=(self.id,))


@shared_task
def save_primarysource(pk, update, *argv, **argd):    
    if not update:
        try:
            ps = PrimarySource.objects.get(id=pk)
            ps.state = ps.PROCESSING
            for graph_name in ["schema", "annotation", "data"]:
                dbName = "{}_{}".format(ps.id, graph_name)
                requests.post(
                    "http://{}:{}/$/datasets".format(settings.JENA_HOST, settings.JENA_PORT),
                    params={"dbName" : dbName, "dbType" : "tdb"},
                    auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
                )
                fname = os.path.join(settings.TEMP_ROOT, "primarysource_{}_{}".format(ps.id, graph_name))
                if os.path.exists(fname):
                    with open(fname + ".meta", "rt") as ifd:
                        content_type = ifd.read()
                    with open(fname, "rb") as ifd:                
                        resp = requests.put(
                            "http://{}:{}/{}/data".format(settings.JENA_HOST, settings.JENA_PORT, dbName),
                            headers={"default" : "", "Content-Type" : content_type},
                            data=ifd,
                            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)                    
                        )
            materials_fname = os.path.join(settings.TEMP_ROOT, "primarysource_{}_materials".format(ps.id))
            if os.path.exists(materials_fname):
                psf = PairtreeStorageFactory()
                with zipfile.ZipFile(materials_fname, "r") as zifd:
                    for zname in zifd.namelist():
                        prefix, fname = os.path.split(zname)
                        name = os.path.splitext(fname)[0] if fname.endswith(".metadata") else fname
                        stream_name = "metadata" if fname.endswith(".metadata") else "data"
                        store = psf.get_store(store_dir=os.path.join(settings.MATERIALS_ROOT, prefix), uri_base="https://cdh.jhu.edu/materials/")
                        obj = store.get_object(name, create_if_doesnt_exist=True)
                        obj.add_bytestream(stream_name, zifd.read(zname))
            ps.state = ps.COMPLETE
        except Exception as e:
            ps.state = ps.ERROR
            ps.message = str(e)
            raise e
        finally:
            for name in ["schema", "annotation", "data", "materials"]:
                fname = os.path.join(settings.TEMP_ROOT, "primarysource_{}_{}".format(ps.id, name))
                if os.path.exists(fname):
                    os.remove(fname)
                if os.path.exists(fname + ".meta"):
                    os.remove(fname + ".meta")
            ps.save()


@receiver(pre_delete, sender=PrimarySource, dispatch_uid="unique enough")
def remove_primarysource(sender, instance, **kwargs):
    if settings.USE_JENA:
        for graph_name in ["schema", "data", "annotation"]:
            requests.delete(
                "http://{}:{}/$/datasets/{}_{}".format(settings.JENA_HOST, settings.JENA_PORT, instance.id, graph_name),
                auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
            )
    else:
        pass


# @receiver(post_save, sender=PrimarySource, dispatch_uid="unique enough")
# def save_primarysource(sender, instance, created, raw, using, update_fields, **kwargs):
#     if created == True:
#         process_primarysource.delay(instance.id)
