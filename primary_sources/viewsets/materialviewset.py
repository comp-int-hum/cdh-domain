import re
import json
import zipfile
import os.path
import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from django.shortcuts import render, get_object_or_404
from pairtree import PairtreeStorageFactory
from rest_framework.viewsets import GenericViewSet, ViewSet
from rest_framework.serializers import ModelSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema
from primary_sources.serializers import MaterialSerializer


logger = logging.getLogger(__name__)


class MaterialViewSet(GenericViewSet):
    serializer_class = MaterialSerializer
    schema = AutoSchema(
        tags=["material"],
        component_name="material",
        operation_id_base="material"
    )
    queryset = []

    def __init__(self, *argv, **argd):
        retval = super(MaterialViewSet, self).__init__(*argv, **argd)
        return retval

    def dispatch(self, request, *argv, prefix=None, name=None, **argd):
        self.prefix = prefix
        self.suffix = name
        return super(MaterialViewSet, self).dispatch(request, *argv, **argd)    

    @action(detail=False, methods=["post"])
    def batch(self, request):
        retvals = []
        psf = PairtreeStorageFactory()
        for mid in request.data.getlist("mids", []):
            toks = mid.split("/")
            prefix = toks[0]
            suffix = "/".join(toks[1:])
            store = psf.get_store(store_dir=os.path.join(settings.MATERIALS_ROOT, prefix), uri_base="{}://{}:{}/materials/".format(settings.PROTO, settings.HOSTNAME, settings.PORT))
            suffix = suffix.replace("+", ":").replace(".", "/")
            obj = store.get_object(suffix, create_if_doesnt_exist=False)
            fnames = obj.list_parts()
            metadata = {}
            files = {}
            for fname in fnames:
                if fname == "metadata":
                    files["cdh_metadata"] = fname
                    #metadata = json.loads(obj.get_bytestream(fname, streamable=True).read())
                elif fname == "data":
                    files["cdh_data"] = fname
                    #with obj.get_bytestream(fname, streamable=True) as ifd:
                    #    content = ifd.read()
                elif fname.endswith(".mets.xml"):
                    files["hathitrust_metadata"] = fname
                elif fname.endswith(".zip"):
                    files["hathitrust_zip"] = fname
                else:
                    #logger.error(fname)
                    for sfname in obj.list_parts(fname):
                        #logger.error(sfname)
                        if sfname.endswith(".mets.xml"):
                            files["hathitrust_metadata"] = os.path.join(fname, sfname)
                        elif sfname.endswith(".zip"):
                            files["hathitrust_data"] = os.path.join(fname, sfname)

                    #raise Exception("Unrecognized stream name: {}".format(fname))
            if "cdh_metadata" in files and "cdh_data" in files:
                metadata = json.loads(obj.get_bytestream(files["cdh_metadata"], streamable=True).read())
                with obj.get_bytestream(files["cdh_data"], streamable=True) as ifd:
                    content = ifd.read()
            elif "hathitrust_metadata" in files and "hathitrust_data" in files:
                metadata = {
                    "content_type" : "text/plain"
                }
                zf = obj.get_bytestream(files["hathitrust_data"], streamable=True)
                document_pages = []
                with zipfile.ZipFile(zf, "r") as zifd:
                    for page in zifd.namelist():
                        document_pages.append(zifd.read(page).decode("utf-8"))                            
                content = "\n".join(document_pages)
            elif "cdh_data" in files:
                with obj.get_bytestream(files["cdh_data"], streamable=True) as ifd:
                    content = ifd.read()
                metadata = {}
            else:
                #logger.error(str(files))
                obj.get_bytestream(files["hathitrust_data"], streamable=True)
                raise Exception()
            #logger.error("FFF: %s", mid)
            retvals.append(
                {
                    "content" : content,
                    "metadata" : metadata,
                    "mid" : mid
                }
            )
        return Response(retvals)
