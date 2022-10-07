import time
import logging
import json
import zipfile
import os.path
from django.db import models
from django.db.models import TextField, ForeignKey, CASCADE, PositiveIntegerField, CharField
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
from cdh.models import CdhModel, User, AsyncMixin
from django.urls import path, reverse
from cdh.decorators import cdh_action
import requests
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import SH, RDF, RDFS, XSD, SDO
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import rdflib
from pairtree import PairtreeStorageFactory


logger = logging.getLogger(__name__)


CDH = Namespace("http://cdh.jhu.edu/materials/")


if settings.USE_CELERY:
    from celery import shared_task
else:
    def shared_task(func):
        return func

named_graphs_query = """
SELECT DISTINCT ?graph where {
  GRAPH ?graph {}
}
"""

named_graph_query = """
SELECT DISTINCT ?s ?p ?o where {
  GRAPH <%s> {?s ?p ?o .}
}
"""

drop_annotation_query = """
DROP GRAPH <http://%s:%s/%s/>
"""
    
class PrimarySource(AsyncMixin, CdhModel):

    def add_annotations(self, graph, identifier):
        # check first for existence?
        resp = requests.put(
            "http://{}:{}/{}/data".format(settings.JENA_HOST, settings.JENA_PORT, self.id),
            params={"graph" : identifier},
            headers={"default" : "", "Content-Type" : "text/turtle"},
            data=graph.serialize(format="turtle").encode("utf-8"),
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)                    
        )

    def sparql(self, query):
        resp = requests.get(
            "http://{}:{}/{}/query".format(settings.JENA_HOST, settings.JENA_PORT, self.id),
            params={"query" : query},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        return resp.json()

    def get_named_graphs(self):
        return [hit["graph"]["value"] for hit in self.sparql(named_graphs_query)["results"]["bindings"]]

    def get_named_graph(self, uri):
        return self.sparql(named_graph_query % uri)
    
    @cdh_action(detail=True, methods=["get"])
    def domain(self):
        try:
            resp = requests.get(
                "http://{}:{}/{}/data".format(settings.JENA_HOST, settings.JENA_PORT, self.id),
                headers={"Accept" : "application/ld+json"},
                params={"graph" : "http://{}:{}/{}/data/domain".format(settings.JENA_HOST, settings.JENA_PORT, self.id)},
                auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
            )
            return json.loads(resp.content.decode("utf-8"))
        except Exception as e:
            return {}

    @cdh_action(detail=True, methods=["get"])
    def annotations(self):
        retval = []
        for uri in self.get_named_graphs():
            if os.path.split(uri)[-1] != "domain":
                retval.append(uri)
        return retval

    def annotation(self, uri):
        return self.sparql(named_graph_query % uri)
    
    @cdh_action(detail=True, methods=["get"])
    def data(self):
        resp = requests.get(
            "http://{}:{}/{}/get".format(settings.JENA_HOST, settings.JENA_PORT, self.id),
            headers={"Accept" : "application/ld+json"},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        return json.loads(resp.content.decode("utf-8"))

    def save(self, domain_file=None, annotations_file=None, data_file=None, materials_file=None, **argd):
        update = self.id and True
        retval = super(PrimarySource, self).save()
        for name, fd in [
                ("domain", domain_file),
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
    primarysource = models.ForeignKey(PrimarySource, on_delete=models.CASCADE, null=False)

    class Meta:
        verbose_name_plural = "Queries"
    
    def __str__(self):
        return self.name

    @cdh_action(detail=True, methods=["get"])
    def perform(self):
        resp = requests.get(
            "http://{}:{}/{}/query".format(settings.JENA_HOST, settings.JENA_PORT, self.primarysource.id),
            params={"query" : self.sparql},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        try:
            return json.loads(resp.content.decode("utf-8"))
        except:
            return {"head" : {"vars" : []}, "results" : {"bindings" : []}}


class Annotation(AsyncMixin, CdhModel):
    query = models.ForeignKey(Query, on_delete=models.CASCADE, null=False)
    app_label = CharField(max_length=100)
    model_class = CharField(max_length=100)
    object_id = PositiveIntegerField()
    
    def save(self, graph=None, *argv, **argd):
        if not self.id:
            retval = super(Annotation, self).save()
            save_annotation.delay(self.id) #, self.app_label, self.model_class, self.object_id)
        return self

    def delete(self, *argv, **argd):
        resp = requests.post(
            "http://{}:{}/{}/update".format(settings.JENA_HOST, settings.JENA_PORT, self.query.primarysource.id),
            data={"update" : drop_annotation_query % (settings.JENA_HOST, settings.JENA_PORT, self.id)},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        super(Annotation, self).delete(*argv, **argd)
        

@shared_task
def save_annotation(ann_id, *argv, **argd):
    ann = Annotation.objects.get(id=ann_id)
    obj = ContentType.objects.get(app_label=ann.app_label, model=ann.model_class).get_object_for_this_type(id=ann.object_id)
    ann.state = ann.PROCESSING
    try:
        obj.apply(
            ann.query.id,
            "http://{}:{}/{}/data".format(settings.JENA_HOST, settings.JENA_PORT, ann.query.primarysource.id),
            str(ann_id)
        )
        ann.state = ann.COMPLETE
    except Exception as e:
        ann.state = ann.ERROR
        ps.message = str(e)
        raise e        
    finally:
        ann.save()


@shared_task
def save_primarysource(pk, update, *argv, **argd):    
    if not update:
        try:
            ps = PrimarySource.objects.get(id=pk)
            ps.state = ps.PROCESSING
            time.sleep(2)
            paths = {}
            for graph_name in ["domain", "data"]:
                fname = os.path.join(settings.TEMP_ROOT, "primarysource_{}_{}".format(ps.id, graph_name))
                if os.path.exists(fname):
                    paths["{}_file".format(graph_name)] = fname                                    
            materials_fname = os.path.join(settings.TEMP_ROOT, "primarysource_{}_materials".format(ps.id))
            
            if len(paths) == 0 and os.path.exists(materials_fname):
                data_graph = Graph()
                data_graph.bind("cdh", CDH)                
                with zipfile.ZipFile(materials_fname, "r") as zifd:
                    for info in zifd.infolist():
                        name = info.filename
                        if not name.endswith(".metadata") and not name.startswith("__MACOSX") and not name.endswith(".DS_Store") and not info.is_dir():
                            
                            #toks = name.split("/")
                            #prefix = toks[0]                            
                            #document_id = "/".join(toks[1:])
                            data_graph.add(
                                (
                                    #CDH[document_id],
                                    rdflib.BNode(),
                                    CDH["materialId"],
                                    rdflib.Literal("uploaded/{}".format(name))
                                    #URIRef("{}://{}:{}/materials/{}/{}".format(settings.PROTO, settings.HOSTNAME, settings.PORT, prefix, document_id))
                                )
                            )
                fname = os.path.join(settings.TEMP_ROOT, "primarysource_{}_data".format(ps.id))
                data_graph.serialize(destination=fname)
                paths["data_file"] = fname
                with open("{}.meta".format(fname), "wt") as ofd:
                    ofd.write("text/turtle")
                
            if os.path.exists(materials_fname):
                psf = PairtreeStorageFactory()
                for s, p, o in data_graph.triples((None, CDH["materialId"], None)):
                    print(o)
                # with zipfile.ZipFile(materials_fname, "r") as zifd:
                #     for info in zifd.infolist():
                #         fname = info.filename
                #         if not name.endswith(".metadata") and not name.startswith("__MACOSX") and not name.endswith(".DS_Store") and not info.is_dir():
                #             prefix = "uploaded"
                #             name = os.path.splitext(fname)[0] if fname.endswith(".metadata") else fname
                #             stream_name = "metadata" if fname.endswith(".metadata") else "data"
                #             store = psf.get_store(store_dir=os.path.join(settings.MATERIALS_ROOT, prefix), uri_base="https://cdh.jhu.edu/materials/")
                #             obj = store.get_object(name, create_if_doesnt_exist=True)
                #             obj.add_bytestream(stream_name, zifd.read(fname))
            dbName = "{}".format(ps.id)
            requests.post(
                "http://{}:{}/$/datasets".format(settings.JENA_HOST, settings.JENA_PORT),
                params={"dbName" : dbName, "dbType" : "tdb"},
                auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
            )
            for graph_name in ["data", "domain"]:
                fname_key = "{}_file".format(graph_name)
                fname = paths.get(fname_key, "")
                if os.path.exists(fname):
                    with open(fname + ".meta", "rt") as ifd:
                        content_type = ifd.read()
                    params = {} if graph_name == "data" else {"graph" : graph_name}
                    with open(fname, "rb") as ifd:
                        resp = requests.put(
                            "http://{}:{}/{}/data".format(settings.JENA_HOST, settings.JENA_PORT, dbName),
                            params=params,
                            headers={"default" : "", "Content-Type" : content_type},
                            data=ifd,
                            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)                    
                        )
            ps.state = ps.COMPLETE
        except Exception as e:
            ps.state = ps.ERROR
            ps.message = str(e)
            raise e
        finally:
            for name in ["domain", "data", "materials"]:
                fname = os.path.join(settings.TEMP_ROOT, "primarysource_{}_{}".format(ps.id, name))
                if os.path.exists(fname):
                   os.remove(fname)
                if os.path.exists(fname + ".meta"):
                   os.remove(fname + ".meta")
            ps.save()


@receiver(pre_delete, sender=PrimarySource, dispatch_uid="unique enough")
def remove_primarysource(sender, instance, **kwargs):
    if settings.USE_JENA:
        requests.delete(
            "http://{}:{}/$/datasets/{}".format(settings.JENA_HOST, settings.JENA_PORT, instance.id),
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
    else:
        pass


#@receiver(pre_delete, sender=Annotation, dispatch_uid="unique enough")
#def remove_annotation(sender, instance, **kwargs):
#    if settings.USE_JENA:
#        pass
    #requests.delete(
    #        "http://{}:{}/$/datasets/{}".format(settings.JENA_HOST, settings.JENA_PORT, instance.id),
    #        auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
    #    )
#    else:
#        pass
    

# @receiver(post_save, sender=PrimarySource, dispatch_uid="unique enough")
# def save_primarysource(sender, instance, created, raw, using, update_fields, **kwargs):
#     if created == True:
#         process_primarysource.delay(instance.id)
