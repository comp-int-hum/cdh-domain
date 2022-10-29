import logging
import os.path
import zipfile
import json
from django.conf import settings
from rest_framework.serializers import ModelSerializer, BaseSerializer, HyperlinkedModelSerializer, HyperlinkedRelatedField
from rest_framework.serializers import ModelSerializer, HiddenField, CurrentUserDefault, HyperlinkedModelSerializer, HyperlinkedIdentityField, ReadOnlyField, FileField, CharField, URLField
import requests
from cdh.serializers import CdhSerializer
from cdh.fields import ActionOrInterfaceField, MonacoEditorField, UploadableTextField
from .models import MachineLearningModel
from .fields import MachineLearningModelInteractionField


logger = logging.getLogger(__name__)


#if settings.USE_CELERY:
#    from celery import shared_task
#else:
#    def shared_task(func):
#        return func


class MachineLearningModelSerializer(CdhSerializer):
    mar_file = FileField(required=False)
    signature_file = FileField(required=False) #UploadableTextField(required=False)
    #output_signature = FileField(required=False) #UploadableTextField(required=False)
    apply_url = ActionOrInterfaceField(
        MachineLearningModelInteractionField(
            detail_endpoint=True,
            endpoint="api:machinelearningmodel-apply",
            language="torchserve_text",
            property_field="apply"
        ),
        view_name="api:machinelearningmodel-apply",
    )

    class Meta:
        model = MachineLearningModel
        fields = ["name", "signature_file", "mar_file", "url", "created_by", "id", "apply_url"]
        view_fields = ["name", "apply_url", "id"]
        edit_fields = ["name", "url", "created_by", "id"]
        create_fields = ["name", "signature_file", "mar_file", "url", "created_by", "id"]

    def create(self, validated_data):
        fields = [f.name for f in MachineLearningModel._meta.fields]
        obj = MachineLearningModel(**{k : v for k, v in validated_data.items() if k in fields})
        #mar_file = validated_data.get("mar_file", None)
        #if mar_file:

        obj.save(
            signature_file=validated_data["signature_file"],
            mar_file=validated_data["mar_file"]
        )
        #url_field=validated_data["url_field"], text_field=validated_data["text_field"], remove_stopwords=validated_data["remove_stopwords"])
        return obj


        #obj = MachineLearningModel.objects.create(name=validated_data["name"], created_by=validated_data["created_by"])
        #task = load_model.delay(obj.id)
        #return obj


# @shared_task
# def load_model(obj_id, *argv, **argd):
#     try:
#         obj = MachineLearningModel.objects.get(id=obj_id)
#         obj.message = "TorchServe is importing the model"
#         with zipfile.ZipFile(os.path.join(settings.MODELS_ROOT, "machinelearningmodel_{}.mar".format(obj.id)), "a") as zfd:
#             with zfd.open("MAR-INF/MANIFEST.json", "r") as ifd:
#                 meta = json.loads(ifd.read())
#             if meta["model"]["handler"] in zfd.namelist():
#                 with zfd.open(meta["model"]["handler"], "r") as ifd:
#                     meta["handler_code"] = ifd.read().decode("utf-8")
#             meta["model"]["modelName"] = str(obj.id)
#             obj.metadata["mar_info"] = {k : v for k, v in meta.items()}
#             with zfd.open("MAR-INF/MANIFEST.json", "w") as ofd:
#                 ofd.write(json.dumps(meta).encode("ascii"))
#         resp = requests.post(
#             "{}/models".format(settings.TORCHSERVE_MANAGEMENT_ADDRESS),
#             params={
#                 "model_name" : obj.id,
#                 "url" : "machinelearningmodel_{}.mar".format(obj.id),
#                 "initial_workers" : 1,
#             },
#         )        
#         if resp.ok:
#             obj.state = obj.COMPLETE
#         else:
#             obj.state = obj.ERROR
#             obj.message = resp.reason
#         obj.save()
#     except Exception as e:
#         obj.state = obj.ERROR
#         obj.message = str(e)
#         obj.save()
#         raise e
    
