# from datetime import datetime
# from django.forms import ModelForm, modelform_factory, FileField
# from django.template.engine import Engine
# from django.template import Context
# import re
# import logging
# from secrets import token_hex as random_token

# from cdh import settings
# from cdh.models import User
# from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
# from django.urls import re_path, reverse
# from django.views.generic.list import ListView, MultipleObjectMixin
# from django.utils.decorators import classonlymethod

# from django.views.generic.base import TemplateView, TemplateResponseMixin, ContextMixin
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
# from django.views.generic import DetailView
# from django.views.generic.edit import CreateView, DeleteView, UpdateView, DeletionMixin, ModelFormMixin, ProcessFormView
from django.views import View
# from django.contrib.auth.models import Group
# from django.core.cache import cache
# from guardian.shortcuts import get_perms, get_objects_for_user, assign_perm, get_users_with_perms, get_groups_with_perms, remove_perm
# from guardian.forms import UserObjectPermissionsForm, GroupObjectPermissionsForm

# from schedule.feeds import CalendarICalendar, UpcomingEventsFeed
# from schedule.models import Calendar
# from schedule.periods import Day, Month, Week, Year
# from schedule.views import (
#     CalendarByPeriodsView,
#     CalendarView,
#     CancelOccurrenceView,
#     CreateEventView,
#     CreateOccurrenceView,
#     DeleteEventView,
#     EditEventView,
#     EditOccurrenceView,
#     EventView,
#     FullCalendarView,
#     OccurrencePreview,
#     OccurrenceView,
#     api_move_or_resize_by_code,
#     api_occurrences,
#     api_select_create,
# )
from django.utils.safestring import mark_safe
# from django.utils.text import slugify
# from django.contrib.auth.decorators import login_required, permission_required
# from . import models, forms
from cdh.widgets import VegaWidget

# if settings.USE_LDAP:
#     from django_auth_ldap.backend import LDAPBackend

# template_engine = Engine.get_default()

# logger = logging.getLogger("django")


class VegaView(SingleObjectMixin, View):
    """
    A VegaView renders a dynamic Vega visualization.  The as_view() method
    accepts the following arguments:

      preamble
      model
      model_attr
      vega_class    
    """
    template = "cdh/simple_interface.html"
    model = None
    vega_class = None
    model_attr = None
    preamble = None

    def render(self, request):        
        w = VegaWidget(vega_class=self.vega_class, preamble=self.preamble)
        retval = w.render("", getattr(self.get_object(), self.model_attr))
        return mark_safe(retval)
    
    def get(self, request, *argv, **argd):
        return render(request, self.template, {"content" : self.render(request)})
