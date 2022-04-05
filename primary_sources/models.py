from django.db import models
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from cdh import settings
from cdh.models import User, AsyncMixin
import requests


class Dataset(models.Model):
    name = models.CharField(max_length=1000)
    def __str__(self):
        return self.name
    #class Meta:
    #    permissions = (
    #        ("manage_dataset", "Full management of the Dataset"),
    #    )

# @receiver(post_save, sender=Dataset, dispatch_uid="unique enough")
# def create_dataset(sender, instance, **kwargs):
#     if settings.USE_JENA:
#         requests.post(
#             "http://{}:{}/$/datasets".format(settings.JENA_HOST, settings.JENA_PORT),
#             params={"dbName" : str(instance.id), "dbType" : "tdb"},
#             auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)
#         )
#     else:
#         pass


# @receiver(pre_delete, sender=Dataset, dispatch_uid="unique enough")
# def remove_dataset(sender, instance, **kwargs):
#     if settings.USE_JENA:
#         requests.delete(
#             "http://{}:{}/$/datasets/{}".format(settings.JENA_HOST, settings.JENA_PORT, instance.id),
#             auth=requests.auth.HTTPBasicAuth(settings.JENA_USER, settings.JENA_PASSWORD)                    
#         )
#     else:
#         pass
