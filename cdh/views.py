import logging
from cdh import settings
from cdh.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import re_path
from django.views.generic.list import ListView
from django.contrib.auth.models import Group

from schedule.feeds import CalendarICalendar, UpcomingEventsFeed
from schedule.models import Calendar
from schedule.periods import Day, Month, Week, Year
from schedule.views import (
    CalendarByPeriodsView,
    CalendarView,
    CancelOccurrenceView,
    CreateEventView,
    CreateOccurrenceView,
    DeleteEventView,
    EditEventView,
    EditOccurrenceView,
    EventView,
    FullCalendarView,
    OccurrencePreview,
    OccurrenceView,
    api_move_or_resize_by_code,
    api_occurrences,
    api_select_create,
)
from django.contrib.auth.decorators import login_required, permission_required
from . import models, forms
if settings.USE_LDAP:
    from django_auth_ldap.backend import LDAPBackend

def index(request):
    context = {
        "slides" : models.Slide.objects.all(),
        "public" : [
            ("about", "About"),
            ("people", "People"),
            ("resources", "Resources"),
            ("events", "Events"),
            ("opportunities", "Opportunities"),
        ],
        "private" : [
            ("primary_sources", "Primary sources"),
            ("topic_modeling", "Topic modeling"),
            #("primary_sources", "Primary sources"),
            #("primary_sources", "Primary sources"),
            #("primary_sources", "Primary sources"),
            #("primary_sources", "Primary sources"),
        ],
    }
    return render(request, 'cdh/index.html', context)

#def about(request):
#    context = {
#    }
#    return render(request, 'cdh/about.html', context)

def people(request):
    if settings.USE_LDAP:
        ld = LDAPBackend()
        users = [ld.populate_user(u.username) for u in models.User.objects.all()] #Group.objects.get(name="Affiliates")
        users = [u for u in users if u != None]
        faculty = [u for u in users if "faculty" in u.ldap_user.group_names]
        postdocs = [u for u in users if "postdoc" in u.ldap_user.group_names]
        students = [u for u in users if "student" in u.ldap_user.group_names]
        affiliates = [u for u in users if "affiliate" in u.ldap_user.group_names]
    else:
        faculty = User.objects.filter(groups__name="faculty")
        postdocs = User.objects.filter(groups__name="postdoc")
        students = User.objects.filter(groups__name="student")
        affiliates = User.objects.filter(groups__name="affiliate")
    context = {
        "faculty" : sorted(faculty, key=lambda x : x.last_name),
        "postdocs" : sorted(postdocs, key=lambda x : x.last_name),
        "students" : sorted(students, key=lambda x : x.last_name),
        "affiliates" : affiliates,
    }
    return render(request, 'cdh/people.html', context)

# def research(request):
#     context = {
#         "research" : models.Research.objects.all(),
#     }
#     return render(request, 'cdh/research.html', context)

# def resources(request):
#     context = {
#         "resources" : models.Resource.objects.all(),
#         "organizations" : models.Organization.objects.all(),
#     }
#     return render(request, 'cdh/resources.html', context)

def events(request):
   context = {
   }
   return render(request, 'cdh/events.html', context)

# @login_required
# def manage_account(request):
#     if request.method == "POST":
#         form = forms.ModifyUserForm(request.POST, request.FILES, instance=request.user)
#         logging.error(request.FILES)
#         if form.is_valid():
#             form.save()
#         return HttpResponseRedirect(redirect_to="/accounts/manage/")
#     else:
#         context = {
#             "form" : forms.ModifyUserForm(instance=request.user)
#         }
#         return render(request, 'cdh/manage_account.html', context)
