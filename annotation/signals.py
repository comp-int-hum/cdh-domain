import logging
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, pre_delete
from turkle.models import Batch, Project, Task, TaskAssignment
from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_users_with_perms, get_groups_with_perms, remove_perm


logger = logging.getLogger()


@receiver(post_save, sender=Task)
def set_permissions(sender, instance, created, *argv, **argd):
    creator = instance.batch.created_by
    if created:
        for perm in ["delete", "change", "view"]:
            assign_perm(
                "{}.{}_{}".format(
                    instance._meta.app_label,
                    perm,
                    instance._meta.model_name
                ),
                creator,
                instance
            )
    logger.info("Set initial permissions on %s", instance)


@receiver(post_save, sender=TaskAssignment)
def set_permissions(sender, instance, created, *argv, **argd):
    creator = instance.task.batch.created_by
    assignee = instance.assigned_to
    if created:
        for perm in ["delete", "change", "view"]:
            assign_perm(
                "{}.{}_{}".format(
                    instance._meta.app_label,
                    perm,
                    instance._meta.model_name
                ),
                creator,
                instance
            )
            assign_perm(
                "{}.{}_{}".format(
                    instance._meta.app_label,
                    perm,
                    instance._meta.model_name
                ),
                assignee,
                instance
            )
    logger.info("Set initial permissions on %s", instance)

