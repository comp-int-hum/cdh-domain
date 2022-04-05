from django.db import models

class Tag(models.Model):
    value = models.CharField(max_length=100)

class Opportunity(models.Model):
    description = models.TextField()
    tags = models.ManyToManyField(Tag)

