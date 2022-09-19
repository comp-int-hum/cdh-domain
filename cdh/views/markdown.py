import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
import markdown


logger = logging.getLogger(__name__)


class MarkdownView(View):
    def get(self, request, *argv, **argd):
        return HttpResponse(markdown.markdown(request.GET["content"]))
    
