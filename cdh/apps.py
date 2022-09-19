from django.apps import AppConfig

class CDHConfig(AppConfig):
    name = 'cdh'
    label = 'cdh'
    verbose_name = "Center for Digital Humanities"

    def ready(self):
        from . import signals
