# from datetime import datetime
# from django.forms import ModelForm, modelform_factory, FileField
# from django.template.engine import Engine
# from django.template import Context
# import re
import logging
# from secrets import token_hex as random_token

# from cdh import settings
# from cdh.models import User
# from django.http import HttpResponse, HttpResponseRedirect
# from django.shortcuts import render, get_object_or_404
# from django.urls import re_path, reverse
# from django.views.generic.list import ListView, MultipleObjectMixin
# from django.utils.decorators import classonlymethod

# from django.views.generic.base import TemplateView, TemplateResponseMixin, ContextMixin
# from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
# from django.views.generic import DetailView
# from django.views.generic.edit import CreateView, DeleteView, UpdateView, DeletionMixin, ModelFormMixin, ProcessFormView
# from django.views import View
# from django.contrib.auth.models import Group
from django.core.cache import cache
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
#from django.utils.safestring import mark_safe
# from django.utils.text import slugify
# from django.contrib.auth.decorators import login_required, permission_required
# from . import models, forms
# from .widgets import VegaWidget

# if settings.USE_LDAP:
#     from django_auth_ldap.backend import LDAPBackend

# template_engine = Engine.get_default()

logger = logging.getLogger("django")


def cdh_cache_method(method):
    def cached_method(*argv, **argd):
        obj = argv[0]
        key = "{}_{}_{}_{}".format(obj._meta.app_label, obj._meta.model_name, obj.id, method.__name__)
        timestamp_key = "TIMESTAMP_{}_{}_{}_{}".format(obj._meta.app_label, obj._meta.model_name, obj.id, method.__name__)
        cache_ts = cache.get(timestamp_key)
        obj_ts = obj.modified_at
        if cache_ts == None or cache_ts < obj_ts:
            logger.info("cache miss for key '{}'".format(key))
            retval = method(*argv, **argd)
            cache.set(timestamp_key, obj_ts, timeout=None)
            cache.set(key, retval, timeout=None)
            return retval
        else:
            logger.info("cache hit for key '{}'".format(key))
            return cache.get(key)
    return cached_method


def cdh_cache_function(func):
    raise Exception("cdh_cache_function not implemented yet!")
    def cached_func(*argv, **argd):
        return func(*argv, **argd)
    return cached_func
