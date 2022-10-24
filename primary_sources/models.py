import time
import re
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
from cdh.decorators import cdh_action, cdh_cache_method
from datetime import datetime
import requests
from rdflib import Graph, URIRef, Namespace
from rdflib.namespace import SH, RDF, RDFS, XSD, SDO
from rdflib.plugins.sparql import prepareQuery
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
SELECT ?s ?p ?o where {
  GRAPH <%s> {?s ?p ?o .}
} limit 10
"""

drop_annotation_query = """
DROP GRAPH <%s>
"""
    
class PrimarySource(AsyncMixin, CdhModel):

    def add_annotations(self, graph, identifier):
        # check first for existence?
        resp = requests.put(
            "http://{}:{}/primarysource_{}/data".format(settings.JENA_HOST, settings.JENA_PORT, self.id),
            params={"graph" : identifier},
            headers={"default" : "", "Content-Type" : "text/turtle"},
            data=graph.serialize(format="turtle").encode("utf-8"),
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)                    
        )

    def sparql(self, query, limit=None, offset=None):
        #orderby [

        pq = prepareQuery(query)
        if limit and "length" not in pq.algebra["p"]:
            query = query + " LIMIT {}".format(limit)
        if offset and ("start" not in pq.algebra["p"] or pq.algebra["p"]["start"] == 0):
            query = query + " OFFSET {}".format(offset)        
        resp = requests.post(
           "http://{}:{}/primarysource_{}/query".format(settings.JENA_HOST, settings.JENA_PORT, self.id),
           data={"query" : query},
           auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        return resp.json()

    def get_named_graphs(self):
        return [hit["graph"]["value"] for hit in self.sparql(named_graphs_query)["results"]["bindings"]]

    def get_named_graph(self, uri):
        return self.sparql(named_graph_query % uri)
    
    @cdh_action(detail=True, methods=["get"])
    #@cdh_cache_method
    def domain(self):
        try:
            resp = requests.get(
                "http://{}:{}/primarysource_{}/data".format(settings.JENA_HOST, settings.JENA_PORT, self.id),
                headers={"Accept" : "application/ld+json"},
                params={"graph" : "http://{}:{}/primarysource_{}/data/domain".format(settings.JENA_HOST, settings.JENA_PORT, self.id)},
                auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
            )
            return json.loads(resp.content.decode("utf-8"))
        except Exception as e:
            return {}

    @cdh_action(detail=True, methods=["get"])
    #@cdh_cache_method
    def annotations(self):
        retval = []        
        for uri in self.get_named_graphs():
            if os.path.split(uri)[-1] != "domain":
                retval.append(uri)
        return retval

    def annotation(self, aid):
        return self.sparql(
            #"""
            #CONSTRUCT { ?s ?p ?o } WHERE {
            #  GRAPH <http://%s:%s/primarysource_%s/data/%s> { ?s ?p ?o . }
            #}
            #""" % (settings.JENA_HOST, settings.JENA_PORT, self.id, aid)
            """
            SELECT ?s ?p ?o WHERE {
              GRAPH <http://%s:%s/primarysource_%s/data/%s> {?s ?p ?o .}
            }
            """ % (settings.JENA_HOST, settings.JENA_PORT, self.id, aid)
        )
        #resp = requests.get(
        #    "http://{}:{}/primarysource_{}/get".format(settings.JENA_HOST, settings.JENA_PORT, self.id),
        #    headers={"Accept" : "application/ld+json"},
        #    params={"graph" : "http://{}:{}/primarysource_{}/data/{}".format(settings.JENA_HOST, settings.JENA_PORT, self.id, aid)},
        #    auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        #)
        #return json.loads(resp.content.decode("utf-8"))

    #return self.sparql(named_graph_query % uri)
    
    @cdh_action(detail=True, methods=["get"])
    #@cdh_cache_method    
    def data(self, limit=None):
        resp = requests.get(
            "http://{}:{}/primarysource_{}/get".format(settings.JENA_HOST, settings.JENA_PORT, self.id),
            headers={"Accept" : "application/ld+json"},
            params={"graph" : "default"},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        return json.loads(resp.content.decode("utf-8"))

    def save(self, domain_file=None, annotations_file=None, data_file=None, materials_file=None, **argd):
        update = self.id and True
        retval = super(PrimarySource, self).save()
        if not update:
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
    def perform(self, limit=None, offset=None):
        sparql = self.sparql
        #if limit and not re.match(r".*limit\s+\d+.*", self.sparql, re.I):
            
        resp = self.primarysource.sparql(sparql, limit=limit, offset=offset)
        return resp
        #resp = requests.post(        
        #    "http://{}:{}/primarysource_{}/query".format(settings.JENA_HOST, settings.JENA_PORT, self.primarysource.id),
        #    data={"query" : sparql},
        #    auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        #)
        #try:
        #    return json.loads(resp.content.decode("utf-8"))
        #except:
        #    return {"head" : {"vars" : []}, "results" : {"bindings" : []}}


class Annotation(AsyncMixin, CdhModel):
    query = models.ForeignKey(Query, on_delete=models.CASCADE, null=False)
    app_label = CharField(max_length=100)
    model_class = CharField(max_length=100)
    object_id = PositiveIntegerField()

    @property
    def jena_id(self):
        return "{proto}://{host}:{port}/primarysource_{psid}/data/{aid}".format(
            proto=settings.JENA_PROTO,
            host=settings.JENA_HOST,
            port=settings.JENA_PORT,
            psid=self.query.primarysource.id,
            aid=self.id
        )
    
    @cdh_action(detail=True, methods=["get"])
    @cdh_cache_method
    def data(self):
        if self.model_class == "topicmodel" or self.model_class == "lexicon":
            vals = self.query.primarysource.sparql(
                """
                PREFIX cdh: <http://cdh.jhu.edu/>
                PREFIX so: <https://schema.org/>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                SELECT ?topic_name ?lex ?name ?prob WHERE {{
                  GRAPH <{jena_id}> {{
                    ?mod so:option ?topic .
                    ?topic so:hasPart ?lex .
                    ?topic so:name ?topic_name .
                    ?lex so:name ?name .
                    OPTIONAL {{ ?lex so:value ?prob . }}
                  }}
                }}
                """.format(
                    jena_id=self.jena_id,
                    host=settings.JENA_HOST,
                    port=settings.JENA_PORT,
                    psid=self.query.primarysource.id,
                    aid=self.id
                )
            )
            model_info = [
                {
                    "topic_name" : x["topic_name"]["value"],
                    "token" : x["name"]["value"],
                    "probability" : x["prob"]["value"] if "prob" in x else None
                } for x in vals["results"]["bindings"]
            ]
            vals = self.query.primarysource.sparql(
                """
                PREFIX cdh: <http://cdh.jhu.edu/>
                PREFIX so: <https://schema.org/>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                SELECT ?mid ?date ?loc ?label ?count WHERE {{
                  GRAPH <{jena_id}> {{
                    ?annotation cdh:labelsDocument ?mid .
                    ?annotation cdh:hasAssignment ?assignment .
                    ?assignment cdh:assignsLabel ?label .
                    ?assignment cdh:hasCount ?count .
                  }}
                  GRAPH <urn:x-arq:DefaultGraph> {{
                    ?pdoc cdh:materialId ?mid .
                    OPTIONAL {{ ?pdoc so:location ?loc . }}
                    OPTIONAL {{ ?pdoc so:datePublished ?date . }}
                  }}
                }}
                """.format(
                    jena_id=self.jena_id,
                    host=settings.JENA_HOST,
                    port=settings.JENA_PORT,
                    psid=self.query.primarysource.id,
                    aid=self.id
                )
            )
            tinputs = sorted(
                [
                    {
                        "weight" : int(i["count"]["value"]),
                        "timestamp" : datetime.fromisoformat(i["date"]["value"]).timestamp() if "date" in i else None,
                        "location" : json.loads(i["loc"]["value"]) if "loc" in i else None,
                        "topic" : i["label"]["value"]
                    } for i in vals["results"]["bindings"]
                ],
                key=lambda x : x["timestamp"]
            )
            min_t, max_t = [tinputs[0]["timestamp"], tinputs[-1]["timestamp"]]
            bucket_count = 200
            window_size = (max_t - min_t) / bucket_count
            counts = {}            
            buckets = [{}] * bucket_count
            for item in tinputs:
                if item["timestamp"]:
                    bucket = min(int((item["timestamp"] - min_t) / window_size), len(buckets) - 1)
                    buckets[bucket][item["topic"]] = buckets[bucket].get(item["topic"], 0.0) + item["weight"]
                    counts[bucket] = counts.get(bucket, 0) + 1
            total = sum(counts.values())            
            combine = []
            combined_total = 0
            while combined_total < 0.9 * total:
                v, k = sorted([(v, k) for k, v in counts.items()])[-1]
                combined_total += v
                combine.append(k)
                counts.pop(k)
            min_b = min(combine)
            max_b = max(combine)
            min_t = min_t + min_b * window_size
            max_t = min_t + (max_b - min_b + 1) * window_size

            bucket_count = 10
            window_size = (max_t - min_t) / bucket_count
            counts = {}            
            buckets = {} #[{}] * bucket_count            
            for i in range(len(tinputs)):
                item = tinputs[i]
                if item["location"]:
                    j = item["location"]["coordinates"][0]
                    lon = sum([x[0] for x in j]) / len(j)
                    lat = sum([x[1] for x in j]) / len(j)
                    tinputs[i]["location"] = [lon, lat]
                if item["timestamp"] and item["timestamp"] >= min_t and item["timestamp"] <= max_t:
                    bucket = min(int((item["timestamp"] - min_t) / window_size), bucket_count - 1)
                    buckets[bucket] = buckets.get(
                        bucket,
                        {
                            "start" : min_t + bucket * window_size,
                            "end" : min_t + (bucket + 1) * window_size,
                            "weights" : {}
                        }
                    )
                    buckets[bucket]["weights"][item["topic"]] = buckets[bucket]["weights"].get(item["topic"], 0.0) + item["weight"]
                    counts[bucket] = counts.get(bucket, 0) + 1
            return ([i for i in tinputs if i.get("location", False)], buckets, model_info)
        #annotations = self.query.primarysource.annotation(self.id)
        #query_output = self.query.perform()
        raise Exception(self.model_class)
        #return (self.model_class, annotations, query_output)
    
    def save(self, graph=None, *argv, **argd):
        if not self.id:
            retval = super(Annotation, self).save()
            save_annotation.delay(self.id) #, self.app_label, self.model_class, self.object_id)
        return self

    def delete(self, *argv, **argd):
        resp = requests.post(
            "{}://{}:{}/primarysource_{}/update".format(settings.JENA_PROTO, settings.JENA_HOST, settings.JENA_PORT, self.query.primarysource.id),
            data={"update" : "DROP GRAPH <{}>".format(self.jena_id)},
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
            "http://{}:{}/primarysource_{}/data".format(settings.JENA_HOST, settings.JENA_PORT, ann.query.primarysource.id),
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
            logger.info("Saving primary source %s...", ps)
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
                            prefix, suffix = name.split("/")
                            bnode = rdflib.BNode()
                            data_graph.add(
                                (
                                    bnode,
                                    CDH["materialId"],
                                    rdflib.Literal("{}/{}".format(prefix, suffix))
                                )
                            )
                            
                fname = os.path.join(settings.TEMP_ROOT, "primarysource_{}_data".format(ps.id))
                data_graph.serialize(destination=fname)
                paths["data_file"] = fname
                with open("{}.meta".format(fname), "wt") as ofd:
                    ofd.write("text/turtle")
                
            if os.path.exists(materials_fname):
                psf = PairtreeStorageFactory()
                with zipfile.ZipFile(materials_fname, "r") as zifd:
                    for i, info in enumerate(zifd.infolist()):
                        if i % 1000 == 0:
                            logger.debug("Adding document #%d", i)
                        fname = info.filename
                        if not fname.endswith(".metadata") and not fname.startswith("__MACOSX") and not fname.endswith(".DS_Store") and not info.is_dir():                            
                            
                            name = os.path.splitext(fname)[0] if fname.endswith(".metadata") else fname
                            prefix, suffix = name.split("/")
                            stream_name = "metadata" if fname.endswith(".metadata") else "data"
                            store = psf.get_store(store_dir=os.path.join(settings.MATERIALS_ROOT, prefix), uri_base="http://cdh.jhu.edu/")
                            obj = store.get_object(suffix, create_if_doesnt_exist=True)
                            obj.add_bytestream(stream_name, zifd.read(fname))
            dbName = "primarysource_{}".format(ps.id)
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
            logger.info("Finished saving primary source %s", ps)
            

@receiver(pre_delete, sender=PrimarySource, dispatch_uid="unique enough")
def remove_primarysource(sender, instance, **kwargs):
    if settings.USE_JENA:
        requests.delete(
            "http://{}:{}/$/datasets/primarysource_{}".format(settings.JENA_HOST, settings.JENA_PORT, instance.id),
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
