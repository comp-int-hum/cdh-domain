import json
import os
import os.path
import logging
import zipfile
from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
try:
    from django.contrib.gis.db.models import CharField, FileField
except:
    from django.db.models import CharField, FileField
from cdh.models import CdhModel, AsyncMixin
from cdh.decorators import cdh_action
import requests
import rdflib


logger = logging.getLogger(__name__)


if settings.USE_CELERY:
    from celery import shared_task
else:
    def shared_task(func):
        return func



class MachineLearningModel(AsyncMixin, CdhModel):
    
    @property
    def info(self, *argv, **argd):
        resp = requests.get("{}/models/{}".format(settings.TORCHSERVE_MANAGEMENT_ADDRESS, self.id))
        return resp.json()

    @property
    def signature(self):
        query = """
        CONSTRUCT { ?s ?p ?o } WHERE {
        GRAPH <http://%s:%s/machinelearningmodel_%s/data/signature> {?s ?p ?o .}
        }
        """ % (settings.JENA_HOST, settings.JENA_PORT, self.id)
        resp = requests.post(
            "http://{}:{}/machinelearningmodel_{}/query".format(settings.JENA_HOST, settings.JENA_PORT, self.id),
            data={"query" : query},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
        g = rdflib.Graph()
        g.parse(data=resp.content)
        return json.loads(g.serialize(format="json-ld"))
    
    @cdh_action(detail=True, methods=["post"])
    def apply(self, *argv, **argd):
        response = requests.post(
            "{}/v2/models/{}/infer".format(settings.TORCHSERVE_INFERENCE_ADDRESS, self.id),
            files=argd
        ).content
        return response
    
    def save(self, mar_file=None, **argd):
        update = self.id and True
        retval = super(MachineLearningModel, self).save()
        if not update:
            with open(os.path.join(settings.MODELS_ROOT, "machinelearningmodel_{}.mar".format(self.id)), "wb") as ofd:
                ofd.write(mar_file.read())
            with open(os.path.join(settings.TEMP_ROOT, "machinelearningmodel_signature_{}".format(self.id)), "wb") as ofd:
                ofd.write(argd["signature_file"].read())
            with open(os.path.join(settings.TEMP_ROOT, "machinelearningmodel_signature_{}.meta".format(self.id)), "wt") as ofd:
                ofd.write(argd["signature_file"].content_type)                    
            task = load_model.delay(self.id)
        return retval


@shared_task
def load_model(obj_id, *argv, **argd):
    try:
        obj = MachineLearningModel.objects.get(id=obj_id)
        obj.message = "TorchServe is importing the model"
        with zipfile.ZipFile(os.path.join(settings.MODELS_ROOT, "machinelearningmodel_{}.mar".format(obj.id)), "a") as zfd:
            with zfd.open("MAR-INF/MANIFEST.json", "r") as ifd:
                meta = json.loads(ifd.read())
            if meta["model"]["handler"] in zfd.namelist():
                with zfd.open(meta["model"]["handler"], "r") as ifd:
                    meta["handler_code"] = ifd.read().decode("utf-8")
            meta["model"]["modelName"] = str(obj.id)
            obj.metadata["mar_info"] = {k : v for k, v in meta.items()}
            with zfd.open("MAR-INF/MANIFEST.json", "w") as ofd:
                ofd.write(json.dumps(meta).encode("ascii"))
        resp = requests.post(
            "{}/models".format(settings.TORCHSERVE_MANAGEMENT_ADDRESS),
            params={
                "model_name" : obj.id,
                "url" : "machinelearningmodel_{}.mar".format(obj.id),
                "initial_workers" : 1,
            },
        )        
        if resp.ok:
            obj.state = obj.COMPLETE
        else:
            obj.state = obj.ERROR
            obj.message = resp.reason
        obj.save()
        dbName = "machinelearningmodel_{}".format(obj.id)
        resp = requests.post(
            "http://{}:{}/$/datasets".format(settings.JENA_HOST, settings.JENA_PORT),
            params={"dbName" : dbName, "dbType" : "tdb"},
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )        
        fname = os.path.join(settings.TEMP_ROOT, "machinelearningmodel_signature_{}".format(obj.id))
        with open(fname + ".meta", "rt") as ifd:
            content_type = ifd.read()
        with open(fname, "rt") as ifd:
            resp = requests.put(
                "http://{}:{}/{}/data".format(settings.JENA_HOST, settings.JENA_PORT, dbName),
                params={"graph" : "signature"},
                headers={"default" : "", "Content-Type" : content_type},
                data=ifd,
                auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)                    
            )
    except Exception as e:
        obj.state = obj.ERROR
        obj.message = str(e)
        obj.save()
        raise e
    finally:
        fname = os.path.join(settings.TEMP_ROOT, "machinelearningmodel_signature_{}".format(obj.id))
        if os.path.exists(fname):
            os.remove(fname)
        if os.path.exists(fname + ".meta"):
            os.remove(fname + ".meta")
        obj.save()


@receiver(pre_delete, sender=MachineLearningModel, dispatch_uid="unique enough")
def remove_machinelearningmodel(sender, instance, **kwargs):
    if settings.USE_JENA:
        requests.delete(
            "http://{}:{}/$/datasets/machinelearningmodel_{}".format(settings.JENA_HOST, settings.JENA_PORT, instance.id),
            auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
        )
    else:
        pass
