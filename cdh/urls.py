from . import settings
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from django.views.generic.list import ListView

from django_registration.backends.activation.views import RegistrationView
from . import forms
from .admin import site as admin_site
from .views import CdhView
from .models import User
from . import views
from django.conf.urls.static import static

urlpatterns = [
    path("{}/".format(k), getattr(views, k) if hasattr(views, k) else include("{}.urls".format(k)), name=k) for k, v in settings.BUILTIN_PAGES.items()
] + [
    path('', views.index, name="index"),
    path('slides/<int:sid>/', views.slide_detail, name="slide"),
    path('manage/', admin_site.urls, name="manage"),
    path('schedule/', include('schedule.urls')),
    #path('vega/', include('vega.urls'), name="vega"),
    path('accounts/register/',
        RegistrationView.as_view(
            form_class=forms.UserForm,
        ),
        name='django_registration_register',
    ),
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path(
        'accounts/manage/<int:pk>/',
        CdhView.as_view(
            model=User,
            fields=["first_name", "last_name", "homepage", "photo", "title", "description"],
            can_update=True,
        ),
        name="manage_account"
    ),
] + [path("{}/".format(k), include("{}.urls".format(k))) for k, v in settings.APPS.items()]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))

