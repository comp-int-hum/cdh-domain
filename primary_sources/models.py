import json
import zipfile
import os.path
from django.db import models
from django.db.models import TextField
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
from cdh.models import CdhModel, User, AsyncMixin
from django.urls import path, reverse
from cdh.decorators import cdh_action
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

    @cdh_action(detail=True, methods=["get"])
    def schema(self):
        resp = requests.get(
            "http://{}:{}/{}_{}/get".format(settings.JENA_HOST, settings.JENA_PORT, self.id, "schema"),
            headers={"Accept" : "application/ld+json"},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        return json.loads(resp.content.decode("utf-8"))

    @cdh_action(detail=True, methods=["get"])
    def annotations(self):
        resp = requests.get(
            "http://{}:{}/{}_{}/get".format(settings.JENA_HOST, settings.JENA_PORT, self.id, "annotations"),
            headers={"Accept" : "application/ld+json"},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        return resp.content.decode("utf-8")
    
    @cdh_action(detail=True, methods=["get"])
    def data(self):
        resp = requests.get(
            "http://{}:{}/{}_{}/get".format(settings.JENA_HOST, settings.JENA_PORT, self.id, "data"),
            headers={"Accept" : "application/ld+json"},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        return resp.content.decode("utf-8")

    def save(self, schema_file=None, annotations_file=None, data_file=None, materials_file=None, **argd):
        update = self.id and True
        retval = super(PrimarySource, self).save()                    
        for name, fd in [
                ("schema", schema_file),
                ("annotations", annotations_file),
                ("data", data_file),
                ("materials", materials_file)
        ]:
            if fd != None:
                with open(os.path.join(settings.TEMP_ROOT, "primarysource_{}_{}".format(self.id, name)), "wb") as ofd:
                    ofd.write(fd.read())
                with open(os.path.join(settings.TEMP_ROOT, "primarysource_{}_{}.meta".format(self.id, name)), "wt") as ofd:
                    ofd.write(fd.content_type)
        save_primarysource.delay(self.id, update)
        return retval
                    

class Query(CdhModel):    
    sparql = TextField()
    primary_source = models.ForeignKey(PrimarySource, on_delete=models.CASCADE, null=False)

    class Meta:
        verbose_name_plural = "Queries"
    
    def __str__(self):
        return self.name

    @cdh_action(detail=True, methods=["get"])    
    def perform(self):
        resp = requests.get(
            "http://{}:{}/{}_{}/query".format(settings.JENA_HOST, settings.JENA_PORT, self.primary_source.id, "data"),
            params={"query" : self.sparql},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        try:
            return json.loads(resp.content.decode("utf-8"))
        except:
            return {"head" : {"vars" : []}, "results" : {"bindings" : []}}


@shared_task
def save_primarysource(pk, update, *argv, **argd):    
    if not update:
        try:
            ps = PrimarySource.objects.get(id=pk)
            ps.state = ps.PROCESSING
            for graph_name in ["schema", "annotations", "data"]:
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
            for name in ["schema", "annotations", "data", "materials"]:
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
