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


class SparqlView(View):
    def get(self, request, *argv, **argd):
        query_id = int(request.GET["pk"])
        primary_source_id = Query.objects.get(id=query_id).primary_source.id
        query_text = request.GET["interaction"]
        if not re.match(r".*limit\s+\d+\s*$", query_text, re.I):
            query_text = query_text + " limit 100"
        try:
            query = prepareQuery(query_text)
        except:
            return HttpResponse("Invalid SPARQL query")
        resp = requests.get(
            "http://{}:{}/{}_{}/query".format(settings.JENA_HOST, settings.JENA_PORT, primary_source_id, "data"),
            params={"query" : query_text},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        j = json.loads(resp.content.decode("utf-8"))        
        links = j["head"].get("link", [])
        boolean = j.get("boolean", None)
        variables = j["head"].get("vars", [])
        # bnode literal uri
        ctx = {
            "variables" : variables,
            "bindings" : [[r.get(v, {}).get("value", "").split("/")[-1].split("#")[-1] for v in variables] for r in j.get("results", {}).get("bindings", [])]
        }
        return render(request, "cdh/sparql_results.html", ctx)

    
