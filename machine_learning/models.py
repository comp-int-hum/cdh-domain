import logging
from django.conf import settings
try:
    from django.contrib.gis.db.models import CharField, FileField
except:
    from django.db.models import CharField, FileField
from cdh.models import CdhModel, AsyncMixin
from cdh.decorators import cdh_action
import requests


logger = logging.getLogger(__name__)


class MachineLearningModel(AsyncMixin, CdhModel):
    #version = CharField(max_length=200, null=True)
    #mar_url = CharField(max_length=2000, null=True)
    #mar_file = FileField(null=True, upload_to="models")
    
    @property
    def info(self, *argv, **argd):
        resp = requests.get("{}/models/{}".format(settings.TORCHSERVE_MANAGEMENT_ADDRESS, self.id))
        return resp.json()

    @cdh_action(detail=True, methods=["post"])
    def apply(self, *argv, **argd):
        print(123123)
        response = requests.post(
            "{}/v2/models/{}/infer".format(settings.TORCHSERVE_INFERENCE_ADDRESS, self.id),
            files=argd
        ).content
        return response
    
