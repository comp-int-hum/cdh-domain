from django.apps import AppConfig


class MachineLearningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'machine_learning'
    
    def ready(self):
        from . import signals
