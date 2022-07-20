import json
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from cdh import settings
from . import models
from . import forms
import requests
import rdflib
from rdflib.tools.rdf2dot import rdf2dot
import io
import json
from cdh import settings
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from primary_sources.models import PrimarySource
import requests
from guardian.shortcuts import get_objects_for_user
#from .vega import PrimarySourceRelationalGraph


def index(request):
    spec = {
        "children" : [
            {
                "child_form" : forms.DatasetForm,
                "children" : [{"object" : o} for o in models.Dataset.objects.all()],
            },
        ],
    }
    context = {
        "formset" : AccordionFormSet(
            spec,
            request.user,
            prefix="primary"
        )
    }
    return render(request, "primary_sources/index.html", context)


#def dataset_relational_graph(request, pk):
#    pass

def primarysource_relational_graph_spec(request, pk):    
#     query = """
# PREFIX owl: <http://www.w3.org/2002/07/owl#>
# PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
# PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
# PREFIX schema: <https://schema.org/>
# PREFIX : <http://www.w3.org/TR/2003/PR-owl-guide-20031209/wine#>
# SELECT DISTINCT ?st ?r ?ot datatype(?o)
# WHERE {
#   ?s rdf:type ?st .
#   ?s ?r ?o .
#   OPTIONAL { ?o rdf:type ?ot }
# }
#         """
#     resp = requests.get(
#         "http://{}:{}/{}_{}/query".format(settings.JENA_HOST, settings.JENA_PORT, dataset_id, "data"),
#         #headers={"Accept" : "text/turtle"},
#         params={"query" : query},
#         auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
#     )
#     j = json.loads(resp.content.decode("utf-8"))
#     entities = set()
#     relationships = []
#     properties = []
#     for row in j["results"]["bindings"]:
#         st = row["st"]["value"].split("/")[-1]
#         rel = row["r"]["value"].split("#")[-1].split("/")[-1]
#         entities.add(st)
#         if "ot" in row:
#             ot = row["ot"]["value"].split("/")[-1]
#             entities.add(ot)
#             relationships.append({"source" : st, "target" : ot, "label" : rel})
#         else:
#             properties.append({"source" : st, "label" : rel})
    
#     entities = list(entities)    
#     relationships = [{"source_label" : rel["source"], "source" : entities.index(rel["source"]), "target_label" : rel["target"], "target" : entities.index(rel["target"]), "label" : rel["label"]} for rel in relationships]


    # relationship_query = """
    # PREFIX owl: <http://www.w3.org/2002/07/owl#>
    # PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    # PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>    
    # SELECT DISTINCT ?parent ?child
    # WHERE {
    #     ?child rdfs:subClassOf+ ?parent .
    #     FILTER (!isBlank(?parent))
    # }
    # """
    # hierarchy = {}
    # resp = requests.get(
    #    "http://{}:{}/{}_{}/query".format(settings.JENA_HOST, settings.JENA_PORT, dataset_id, "schema"),
    #    params={"query" : relationship_query},
    #    auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
    # )
    # j = json.loads(resp.content.decode("utf-8"))
    # for row in j["results"]["bindings"]:
    #     child = row["child"]["value"]
    #     parent = row["parent"]["value"]
    #     hierarchy[child] = hierarchy.get(child, []) + [parent]
    #entities, relationships, properties = [{"entity_label" : l} for l in enumerate(['Organization', 'Person', 'CreativeWork'])], [{'source_label': 'CreativeWork', 'source': 2, 'target_label': 'Person', 'target': 1, 'relationship_label': 'creator'}, {'source_label': 'CreativeWork', 'source': 2, 'target_label': 'Organization', 'target': 0, 'relationship_label': 'publisher'}], [{'entity_label': 'CreativeWork', 'property_label': 'type'}, {'entity_label': 'CreativeWork', 'property_label': 'datePublished'}, {'entity_label': 'CreativeWork', 'property_label': 'inLanguage'}, {'entity_label': 'CreativeWork', 'property_label': 'name'}, {'entity_label': 'CreativeWork', 'property_label': 'creator'}, {'entity_label': 'CreativeWork', 'property_label': 'position'}, {'entity_label': 'Person', 'property_label': 'type'}, {'entity_label': 'Person', 'property_label': 'birthDate'}, {'entity_label': 'Person', 'property_label': 'familyName'}, {'entity_label': 'Person', 'property_label': 'givenName'}, {'entity_label': 'Person', 'property_label': 'deathDate'}, {'entity_label': 'Organization', 'property_label': 'type'}, {'entity_label': 'Organization', 'property_label': 'name'}, {'entity_label': 'Organization', 'property_label': 'location'}]
    entities, relationships, properties = [{"entity_label" : l} for l in ['Organization', 'Person', 'CreativeWork']], [{'source_label': 'CreativeWork', 'target_label': 'Person', 'relationship_label': 'creator'}, {'source_label': 'CreativeWork', 'target_label': 'Organization', 'relationship_label': 'publisher'}], [{'entity_label': 'CreativeWork', 'property_label': 'datePublished'}, {'entity_label': 'CreativeWork', 'property_label': 'inLanguage'}, {'entity_label': 'CreativeWork', 'property_label': 'name'}, {'entity_label': 'CreativeWork', 'property_label': 'position'}, {'entity_label': 'Person', 'property_label': 'birthDate'}, {'entity_label': 'Person', 'property_label': 'familyName'}, {'entity_label': 'Person', 'property_label': 'givenName'}, {'entity_label': 'Person', 'property_label': 'deathDate'}, {'entity_label': 'Organization', 'property_label': 'name'}, {'entity_label': 'Organization', 'property_label': 'location'}]    
    #entities, relationships, properties = ['CreativeWork', 'Organization', 'Person'], [{'source': 0, 'target': 2, 'label': 'creator'}, {'source': 0, 'target': 1, 'label': 'publisher'}], [{'source': 'CreativeWork', 'label': 'type'}, {'source': 'CreativeWork', 'label': 'datePublished'}, {'source': 'CreativeWork', 'label': 'inLanguage'}, {'source': 'CreativeWork', 'label': 'name'}, {'source': 'CreativeWork', 'label': 'creator'}, {'source': 'CreativeWork', 'label': 'position'}, {'source': 'Person', 'label': 'type'}, {'source': 'Person', 'label': 'birthDate'}, {'source': 'Person', 'label': 'familyName'}, {'source': 'Person', 'label': 'givenName'}, {'source': 'Person', 'label': 'deathDate'}, {'source': 'Organization', 'label': 'type'}, {'source': 'Organization', 'label': 'name'}, {'source': 'Organization', 'label': 'location'}]
    retval = PrimarySourceRelationalGraph(entities, relationships, properties).json
    #with open("temp.json", "wt") as ofd:
    #    ofd.write(json.dumps(retval, indent=4))
    return JsonResponse(retval)


