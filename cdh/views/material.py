import re
import json
import os.path
import logging
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from django.shortcuts import render, get_object_or_404
from pairtree import PairtreeStorageFactory


class MaterialView(View):
    
    def dispatch(self, request, *argv, prefix=None, name=None, **argd):
        self.prefix = prefix
        self.suffix = name
        return super(MaterialView, self).dispatch(request, *argv, **argd)
        
    def get(self, request, *argv, **argd):
        psf = PairtreeStorageFactory()
        store = psf.get_store(store_dir=os.path.join(settings.MATERIALS_ROOT, self.prefix), uri_base="{}://{}:{}/materials/".format(settings.PROTO, settings.HOSTNAME, settings.PORT))
        obj = store.get_object(self.suffix, create_if_doesnt_exist=False)
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
                raise Exception("Unrecognized stream name: {}".format(fname))
        if "cdh_metadata" in files and "cdh_data" in files:
            metadata = json.loads(obj.get_bytestream(files["cdh_metadata"], streamable=True).read())
            with obj.get_bytestream(files["cdh_data"], streamable=True) as ifd:
                content = ifd.read()
        elif "hathitrust_metadata" in files and "hathitrust_data" in files:
            metadata = {
                "content_type" : "text/plain"
            }
            zf = o.get_bytestream(os.path.join(part, files["hathitrust_data"]), streamable=True)
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
            o.get_bytestream(os.path.join(part, files["hathitrust_data"]), streamable=True)
            raise Exception()
        return HttpResponse(content, content_type=metadata.get("content_type", "unknown"))
