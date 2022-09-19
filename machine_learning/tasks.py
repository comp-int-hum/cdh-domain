import logging
from cdh import settings
from .models import MachineLearningModel
import requests


logger = logging.getLogger(__name__)


if settings.USE_CELERY:
    from celery import shared_task
else:
    def shared_task(func):
        return func


@shared_task
def load_model(obj_id, *argv, **argd):
    try:
        obj = MachineLearningModel.objects.get(id=obj_id)
        obj.message = "TorchServe is importing the model"
        if not obj.mar_url:
            obj.mar_url = obj.mar_file.url
        obj.save()            
        resp = requests.post(
            "{}/models".format(settings.TORCHSERVE_MANAGEMENT_ADDRESS),
            params={
                "model_name" : obj.id,
                "url" : "{}://{}:{}{}".format(settings.proto, settings.HOSTNAME, settings.PORT, obj.mar_url),
                "initial_workers" : 1,                
            },
        )
        if resp.ok:
            obj.state = obj.COMPLETE
        else:
            obj.state = obj.ERROR
            obj.message = resp.reason
        obj.save()
    except Exception as e:
        obj.state = obj.ERROR
        obj.message = str(e)
        obj.save()
        raise e
