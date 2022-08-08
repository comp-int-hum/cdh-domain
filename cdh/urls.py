from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.urls import re_path, include
from django.views.generic.list import ListView
from django_registration.backends.activation.views import RegistrationView
from django.conf.urls.static import static
from . import views
from .settings import MEDIA_URL, MEDIA_ROOT, STATIC_URL, STATIC_ROOT, BUILTIN_PAGES, APPS, DEBUG
from .forms import UserForm
from .admin import site as admin_site
from .views import BaseView, index, slide_detail
from .models import User


urlpatterns = [
    path("{}/".format(k), getattr(views, k) if hasattr(views, k) else include("{}.urls".format(k)), name=k) for k, v in BUILTIN_PAGES.items()
] + [
    path('', index, name="index"),
    path('slides/<int:sid>/', views.slide_detail, name="slide"),
    path('accounts/register/',
        RegistrationView.as_view(
            form_class=UserForm,
        ),
        name='django_registration_register',
    ),
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path(
        'accounts/manage/<int:pk>/',
        BaseView.as_view(
            model=User,
            fields=["first_name", "last_name", "homepage", "photo", "title", "description"],
            can_update=True,
        ),
        name="manage_account"
    ),
] + [path("{}/".format(k), include("{}.urls".format(k))) for k, v in APPS.items()]


if DEBUG:
    urlpatterns += static(MEDIA_URL, document_root=MEDIA_ROOT)
    urlpatterns += static(STATIC_URL, document_root=STATIC_ROOT)
    urlpatterns.append(path('__debug__/', include('debug_toolbar.urls')))
