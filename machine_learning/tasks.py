from cdh import settings
from .models import MachineLearningModel
import requests


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
        obj.save()
        resp = requests.post(
            "{}/models".format(settings.TORCHSERVE_MANAGEMENT_ADDRESS),
            params={
                "model_name" : obj.name,
                "url" : obj.url,
                "initial_workers" : 1,                
            },
        )
        completion = requests.post
        obj.state = obj.COMPLETE
        obj.save()
    except Exception as e:
        obj.state = obj.ERROR
        obj.message = str(e)
        obj.save()
        raise e
