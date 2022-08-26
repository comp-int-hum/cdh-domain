import re
import json
import os.path
import logging
from cdh import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from django.shortcuts import render, get_object_or_404
from pairtree import PairtreeStorageFactory


class MaterialView(View):
    
    def dispatch(self, request, *argv, prefix=None, name=None, **argd):
        print(name, argd)
        self.prefix = prefix
        self.name = name
        return super(MaterialView, self).dispatch(request, *argv, **argd)
        
    def get(self, request, *argv, **argd):
        psf = PairtreeStorageFactory()
        store = psf.get_store(store_dir=os.path.join(settings.MATERIALS_ROOT, self.prefix), uri_base="https://cdh.jhu.edu/materials/")
        obj = store.get_object(self.name, create_if_doesnt_exist=False)
        fnames = obj.list_parts()
        metadata = {}
        for fname in fnames:
            if fname == "metadata":
                metadata = json.loads(obj.get_bytestream(fname, streamable=True).read())
            elif fname == "data":
                with obj.get_bytestream(fname, streamable=True) as ifd:
                    content = ifd.read()
            else:
                raise Exception("Unrecognized stream name: {}".format(fname))
        return HttpResponse(content, content_type=metadata.get("content_type", "unknown"))
