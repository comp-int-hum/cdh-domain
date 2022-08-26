from cdh import settings
from django.db import models
from django.urls import path, reverse
from cdh.models import CdhModel, AsyncMixin
import requests


class MachineLearningModel(AsyncMixin, CdhModel):
    version = models.CharField(max_length=200, null=True)
    url = models.CharField(max_length=2000, null=True)
    
    def get_absolute_url(self):
        return reverse("machine_learning:machinelearningmodel_detail", args=(self.id,))

    def __str__(self):
        return self.name

    @property
    def info(self, *argv, **argd):
        resp = requests.get("{}/models/{}".format(settings.TORCHSERVE_MANAGEMENT_ADDRESS, self.name))
        return resp.json()
        
    class Meta:
        unique_together = [["name", "version"]]
