from . import settings
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from django.views.generic.list import ListView

from django_registration.backends.activation.views import RegistrationView
from . import forms
from .admin import site as admin_site

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
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path("{}/".format(k), getattr(views, k) if hasattr(views, k) else include("{}.urls".format(k)), name=k) for k, v in settings.BUILTIN_PAGES.items()
] + [
    path('', views.index, name="index"),
    path('slides/<int:sid>/', views.slide_detail, name="slide"),
    path('manage/', admin_site.urls, name="manage"),
    path('schedule/', include('schedule.urls')),
    path('vega/', include('vega.urls'), name="vega"),
    path('accounts/register/',
        RegistrationView.as_view(
            form_class=forms.UserForm,
        ),
        name='django_registration_register',
    ),
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
] + [path("{}/".format(k), include("{}.urls".format(k))) for k, v in settings.PRIVATE_APPS.items()] + [path("{}/".format(k), include("{}.urls".format(k))) for k, v in settings.PUBLIC_APPS.items()]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

