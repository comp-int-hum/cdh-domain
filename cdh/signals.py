import logging
from django.contrib.auth import get_user_model
from django_registration.signals import user_activated
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm, get_anonymous_user
from .models import CdhModel


logger = logging.getLogger()


@receiver(post_save)
def post_save_callback(sender, instance, created, raw, using, update_fields, *argv, **argd):
    User = get_user_model()
    anon = get_anonymous_user()
    if created and isinstance(instance, (CdhModel, get_user_model())):
        assign_perm(
            "{}.{}_{}".format(
                instance._meta.app_label,
                "view",
                instance._meta.model_name
            ),
            anon,
            instance
        )
        for perm in ["delete", "change", "view"]:
            assign_perm(
                "{}.{}_{}".format(
                    instance._meta.app_label,
                    perm,
                    instance._meta.model_name
                ),
                instance if isinstance(instance, get_user_model()) else instance.created_by,
                instance
            )
        logger.info("Set initial permissions for %s", instance)
