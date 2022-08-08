import os
import os.path
from django.db import models
from django.urls import path, reverse
from cdh.models import CdhModel
from cdh import settings
import requests


class MachineLearningModel(CdhModel):
    version = models.CharField(max_length=200, null=True)
    url = models.CharField(max_length=2000, null=True)
    
    def get_absolute_url(self):
        return reverse("machine_learning:machinelearningmodel_detail", args=(self.id,))

    def __str__(self):
        return self.name

    def save(self, *argv, **argd):
        # make async, raise errors, etc
        resp = requests.post(
            "{}/models".format(settings.TORCHSERVE_MANAGEMENT_ADDRESS),
            params={
                "model_name" : self.name,
                "url" : self.url,
                "initial_workers" : 1,
                
            },
        )
        super(MachineLearningModel, self).save(*argv, **argd)

    def delete(self, *argv, **argd):
        model_file = "{}/models/{}".format(settings.DATA_DIR, os.path.basename(self.url))
        try:
            os.remove(model_file)
        except:
            pass
        for inf in self.info:            
            resp = requests.delete("{}/models/{}/{}".format(settings.TORCHSERVE_MANAGEMENT_ADDRESS, inf["modelName"], inf["modelVersion"]))
        super(MachineLearningModel, self).delete(*argv, **argd)

    @property
    def info(self, *argv, **argd):
        resp = requests.get("{}/models/{}".format(settings.TORCHSERVE_MANAGEMENT_ADDRESS, self.name))
        return resp.json()
        
    class Meta:
        unique_together = [["name", "version"]]
