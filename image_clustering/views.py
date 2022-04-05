from django.shortcuts import render
from django.http import HttpResponse
from guardian.shortcuts import get_objects_for_user
from . import models

def index(request):
    context = {
        "image_sets" : models.ImageSet.objects.all(),
    }
    return render(request, "image_clustering/index.html", context)
