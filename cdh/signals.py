from django_registration.signals import user_activated
from django.dispatch import receiver



@receiver(user_activated)
def callback(sender, user, request, **kwargs):
    pass
