from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, pre_delete
from turkle.models import Batch, Project

@receiver(post_save, sender=Batch)
def set_permissions(sender, instance, created, *argv, **argd):
    print(100, created)
