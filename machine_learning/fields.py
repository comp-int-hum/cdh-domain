import logging
from secrets import token_hex as random_token
from django.conf import settings
from django.urls import path, reverse
from rest_framework.serializers import Field, CharField, HyperlinkedIdentityField, HyperlinkedRelatedField, RelatedField
from cdh.fields import MonacoEditorField
from .models import MachineLearningModel


logger = logging.getLogger(__name__)


class ObjectDetectionField(Field):
    
    def __init__(self, object_id, *argv, **argd):
        self.field_name = "tabular_{}".format(random_token(6))
        self.style = {}
        self.style["base_template"] = "image.html"
        self.style["template_pack"] = "cdh/template_pack"
        self.style["interactive"] = True
        model = MachineLearningModel.objects.get(id=object_id)
        self.style["endpoint_url"] = reverse("api:machinelearningmodel-apply", args=(model.id,))
    
    def get_default_value(self):
        return None


class MachineLearningModelInteractionField(MonacoEditorField):

    def get_actual_field(self, parent_style, *argv, **argd):
        model = MachineLearningModel.objects.get(id=parent_style["object_id"])
        handler = model.metadata["mar_info"]["model"]["handler"]
        logger.info("Selecting an interface for model with handler '%s'", handler)
        print(handler)
        if handler == "object_detector":
            return ObjectDetectionField(parent_style["object_id"])
        elif handler == "image_classifier":
            pass
        elif handler == "text_classifier":
            pass
        elif handler == "image_segmenter":
            pass
        elif handler == "text_generator":
            pass
        else:            
            return self
    
    def __init__(self, *argv, **argd):
        retval = super(MachineLearningModelInteractionField, self).__init__(*argv, **argd)
        self.style["hide_label"] = True
        self.style["interactive"] = True
