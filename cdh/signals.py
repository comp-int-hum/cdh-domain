import logging
from django.contrib.auth import get_user_model
from django_registration.signals import user_activated
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from guardian.shortcuts import assign_perm
from .models import CdhModel


logger = logging.getLogger()


User = get_user_model()


@receiver(user_activated)
def callback(sender, user, request, **kwargs):
    pass


@receiver(post_save)
def post_save_callback(sender, instance, created, raw, using, update_fields, *argv, **argd):

    if created and hasattr(instance, "created_by"):
        for perm in ["delete", "change", "view"]:
            print(
                "{}.{}_{}".format(
                    instance._meta.app_label,
                    perm,
                    instance._meta.model_name
                ),
                instance.created_by,
                instance
            )

            assign_perm(
                "{}.{}_{}".format(
                    instance._meta.app_label,
                    perm,
                    instance._meta.model_name
                ),
                instance.created_by,
                instance
            )
        # u = User.objects.get(username="AnonymousUser")
        # assign_perm(
        #     "{}.view_{}".format(
        #         instance._meta.app_label,
        #         perm,
        #         instance._meta.model_name
        #     ),
        #     u,
        #     instance
        # )
        logger.info("Set initial permissions for %s", instance)
