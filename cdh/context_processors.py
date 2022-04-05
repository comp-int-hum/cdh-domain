from django.conf import settings
from cdh.models import User
from django.contrib.flatpages.models import FlatPage
import re

def app_directory(request):
    return {
        "flat_pages" : [p for p in FlatPage.objects.all() if re.match(r"^\/[^\/]+\/$", p.url)],
        "is_admin" : request.user.is_staff,
        "private_apps" : settings.PRIVATE_APPS,
        "public_apps" : settings.PUBLIC_APPS,
    }
