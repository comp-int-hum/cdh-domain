from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

@login_required(login_url="/accounts/login/")
def index(request):
    context = {
    }
    return render(request, "starcoder_wrapper/index.html", context)
