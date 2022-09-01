import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
import markdown


class MarkdownView(View):
    def get(self, request, *argv, **argd):
        return HttpResponse(markdown.markdown(request.GET["interaction"]))
    
