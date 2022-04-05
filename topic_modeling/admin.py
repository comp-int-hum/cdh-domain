from django.contrib import admin
from .models import model_classes

for x in model_classes:
    admin.site.register(x)
