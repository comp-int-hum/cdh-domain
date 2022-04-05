from django.db import models
from cdh.models import User, AsyncMixin


class ImageSet(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    data = models.FileField(upload_to="image_sets")
    def get_absolute_url(self):
        return reverse("image_clustering:image_set_detail", args=(self.id,))

    
class Image(models.Model):
    name = models.CharField(max_length=200)
    data = models.FileField(upload_to="images")
    image_set = models.ForeignKey(ImageSet, on_delete=models.CASCADE)
    def get_absolute_url(self):
        return reverse("image_clustering:image_detail", args=(self.id,))


class VisionModel(models.Model):
    name = models.CharField(max_length=200)
    data = models.FileField(upload_to="vision_models")
    def get_absolute_url(self):
        return reverse("image_clustering:vision_model_detail", args=(self.id,))


class ModelOutput(AsyncMixin, models.Model):
    name = models.CharField(max_length=200)
    data = models.JSONField()
    def get_absolute_url(self):
        return reverse("image_clustering:model_output_detail", args=(self.id,))

