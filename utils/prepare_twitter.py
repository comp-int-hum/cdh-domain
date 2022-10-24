import gzip
import re
import uuid
import sys
from datetime import datetime
import shutil
import logging
import csv
import zipfile
import json
from hashlib import md5
import hashlib
from rdflib import Graph, URIRef, BNode, Literal, Namespace
from rdflib.namespace import CSVW, DC, DCAT, DCTERMS, DOAP, \
    FOAF, ODRL2, ORG, OWL, PROF, PROV, RDF, RDFS, SDO, SH, \
    SKOS, SOSA, SSN, TIME, VOID, XMLNS, XSD
from pairtree import PairtreeStorageFactory

CDH = Namespace("http://cdh.jhu.edu/")
GEO = Namespace("http://www.opengis.net/ont/geosparql#")

def process_shapes(graph, shapes):

    def q(v):
        return v if isinstance(v, (URIRef, BNode, Literal)) else CDH[v]
    
    for name, attrs in shapes.items():
        shape = q("{}Shape".format(name))
        graph.add(
            (
                shape,
                SH.closed,
                Literal(True)
            )
        )
        graph.add(
            (
                q(shape),
                q(RDF.type),
                q(SH.NodeShape)
            )
        )
        graph.add(
            (
                q(shape),
                q(SH.targetClass),
                q(name)
            )
        )
        for i, (attr_name, attr_vals) in enumerate(attrs.items()):
            b = BNode()
            graph.add(
                (
                    q(shape),
                    q(SH.property),
                    q(b)
                )
            )
            graph.add(
                (
                    q(b),
                    q(SH.path),
                    q(attr_name)
                )
            )
            for k, v in attr_vals:
                graph.add(
                    (
                        q(b),
                        q(k),
                        q(v)
                    )
                )


if __name__ == "__main__":

    import argparse
    from glob import glob
    import os.path
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", dest="input")
    parser.add_argument("--domain_output", dest="domain_output")
    parser.add_argument("--data_output", dest="data_output")
    parser.add_argument("--materials_output", dest="materials_output")
    args = parser.parse_args()

    domain_graph = Graph()
    domain_graph.bind("cdh", CDH)
    shapes = {
        "User" : {
            SDO.name : [(SH.datatype, XSD.string)],
        },
        "Tweet" : {
            SDO.creator : [(SH["class"], CDH["User"])],
            CDH["materialId"] : [(SH.datatype, XSD.string)],
            #CDH["materialPrefix"] : [(SH.datatype, XSD.string)],
            SDO.inLanguage : [(SH.datatype, XSD.string)],
            SDO.datePublished : [(SH.maxInclusive, Literal("2023", datatype=XSD.dateTime))],
            SDO.location : [(SH.datatype, XSD.string)]
        }
    }
    process_shapes(domain_graph, shapes)
    
    data_graph = Graph()
    data_graph.bind("cdh", CDH)

    zofd = zipfile.ZipFile(args.materials_output, "w")
    with gzip.open(args.input, "rt") as ifd:
        for line in ifd:
            j = json.loads(line)
            
            uid = j["id_str"]
            user = j["user"]["screen_name"]
            date = datetime.strptime(j["created_at"], "%a %b %d %H:%M:%S +0000 %Y")
            bb = None if not j["place"] else json.dumps(j["place"]["bounding_box"])
            text = j["text"]
            lang = j["lang"]
            mid = os.path.join("twitter", uid)
            if bb:
                data_graph.add(
                    (
                        CDH[uid],
                        SDO.location,
                        Literal(
                            bb,
                            datatype=GEO.geoJSONLiteral
                        )
                    )
                )
            for triple in [
                    (
                        CDH[uid],
                        SDO.creator,
                        CDH[user]
                    ),
                    (
                        CDH[uid],
                        SDO.datePublished,
                        Literal(date)
                    ),
                    (
                        CDH[uid],
                        SDO.inLanguage,
                        Literal(lang)
                    ),
                    (
                        CDH[uid],
                        RDF.type,
                        SDO.CreativeWork
                    ),
                    (
                        CDH[uid],
                        CDH["materialId"],
                        Literal(mid)
                    ),
            ]:
                data_graph.add(triple)
                
            arcname = mid
            zofd.writestr(arcname, text)
            zofd.writestr("{}.metadata".format(arcname), json.dumps({"content_type" : "text/plain"}))

    domain_graph.serialize(destination=args.domain_output)
    data_graph.serialize(destination=args.data_output)
