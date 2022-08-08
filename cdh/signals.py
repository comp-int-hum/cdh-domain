from django_registration.signals import user_activated
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import CdhModel


@receiver(user_activated)
def callback(sender, user, request, **kwargs):
    pass

@receiver(post_save)
def post_save_callback(sender, instance, created, raw, using, update_fields, *argv, **argd):
    if isinstance(instance, CdhModel):
        pass
