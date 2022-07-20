from django.conf import settings
from cdh.models import User
from django.contrib.flatpages.models import FlatPage
import re

def app_directory(request):
    top_level = request.path.lstrip("/").split("/")[0]
    return {
        "flat_pages" : [p for p in FlatPage.objects.all() if re.match(r"^\/[^\/]+\/$", p.url)],
        "is_admin" : request.user.is_staff or request.user.groups.filter(name="cdhweb").exists(),
        "apps" : settings.APPS,
        "builtin_pages" : settings.BUILTIN_PAGES,
        "messages" : [],
        "top_level" : top_level,
        "name" : settings.APPS.get(top_level, "Manage")
    }
