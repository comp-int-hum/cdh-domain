import logging
from rest_framework.serializers import ModelSerializer, BaseSerializer, HyperlinkedModelSerializer, HyperlinkedRelatedField
from rest_framework.serializers import ModelSerializer, HiddenField, CurrentUserDefault, HyperlinkedModelSerializer, HyperlinkedIdentityField, ReadOnlyField, FileField, CharField, URLField
from cdh.serializers import CdhSerializer
from cdh.fields import ActionOrInterfaceField, MonacoEditorField
from .models import MachineLearningModel
from .tasks import load_model


logger = logging.getLogger(__name__)


class MachineLearningModelSerializer(CdhSerializer):
    mar_file = FileField(required=False)
    mar_url = URLField(required=False)
    apply_url = ActionOrInterfaceField(
        MonacoEditorField(detail_endpoint=True, endpoint="api:machinelearningmodel-apply", language="torchserve_text", property_field="apply"),
        view_name="api:machinelearningmodel-apply",
        #property_name="apply"
    )

    class Meta:
        model = MachineLearningModel
        fields = ["name", "mar_file", "mar_url", "url", "created_by", "id", "apply_url"]
        view_fields = ["apply_url", "id"]
        edit_fields = ["name", "mar_file", "mar_url", "url", "created_by", "id"]
        create_fields = ["name", "mar_file", "mar_url", "url", "created_by", "id"]

    def create(self, validated_data):
        fields = [f.name for f in MachineLearningModel._meta.fields]
        obj = MachineLearningModel.objects.create(**{k : v for k, v in validated_data.items() if k in fields})
        task = load_model.delay(
            obj.id,
        )
        return obj
