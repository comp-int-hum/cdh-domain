import re
import json
import logging
from cdh import settings
from primary_sources.models import Query
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from django.shortcuts import render, get_object_or_404
from rdflib.plugins.sparql import prepareQuery
import requests


logger = logging.getLogger("cdh")


class SparqlView(View):
    def get(self, request, *argv, **argd):
        query_text = request.GET["query_text"]
        primary_source_id = int(request.GET["primary_source_pk"])
        if not re.match(r".*limit\s+\d+\s*$", query_text, re.I|re.S):
            query_text = query_text.strip() + " limit 10"
        try:
            query = prepareQuery(query_text)
        except Exception as e:
            logger.error(e)
            return HttpResponse("Invalid SPARQL query")
        resp = requests.get(
            "http://{}:{}/{}/query".format(settings.JENA_HOST, settings.JENA_PORT, primary_source_id),
            params={"query" : query_text},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        j = json.loads(resp.content.decode("utf-8"))        
        links = j["head"].get("link", [])
        boolean = j.get("boolean", None)
        variables = j["head"].get("vars", [])
        # bnode literal uri
        # HACK: treats "url" as special
        ctx = {
            "variables" : variables,
            "bindings" : [[(v, r.get(v, {}).get("value", "").replace("cdh.jhu.edu", "{}:{}".format(settings.HOSTNAME, settings.PORT)) if v == "url" else r.get(v, {}).get("value", "").split("/")[-1].split("#")[-1]) for v in variables] for r in j.get("results", {}).get("bindings", [])]
        }
        return render(request, "cdh/sparql_results.html", ctx)

    
