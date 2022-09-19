from django.db.models.signals import post_delete, pre_delete
from cdh import settings
import logging
import os.path
from django.dispatch import receiver
import requests
from .models import MachineLearningModel


logger = logging.getLogger()


@receiver(post_delete, sender=MachineLearningModel)
def delete_model(sender, instance, using, *argv, **argd):
    model_file = instance.mar_file.path
    if os.path.exists(model_file):
        os.remove(model_file)
    else:
        logger.info("No such file to delete: '%s'", model_file)
    for inf in instance.info:
        try:
            resp = requests.delete("{}/models/{}/{}".format(settings.TORCHSERVE_MANAGEMENT_ADDRESS, inf["modelName"], inf["modelVersion"]))
        except:
            logger.info("Problem deleting '%s' from server", inf)
