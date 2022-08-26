import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.forms import ModelForm
from django.http import HttpResponse, HttpResponseRedirect
from django.apps import apps
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views.generic.edit import CreateView, DeleteView, UpdateView, DeletionMixin, ModelFormMixin, ProcessFormView
from guardian.shortcuts import get_perms, get_objects_for_user, get_anonymous_user
from cdh.models import Slide
from .base import BaseView


class SlidesView(BaseView):

    def __init__(self, *argv, **argd):
        super(SlidesView, self).__init__(*argv, **argd)
    
    def get_context_data(self, *argv, **argd):
        ctx = super(SlidesView, self).get_context_data(*argv, **argd)
        ctx["slides"] = get_objects_for_user(get_anonymous_user(), "cdh.view_slide")
        return ctx
        
    def get(self, request, *argv, **argd):
        ctx = self.get_context_data()
        return render(request, "cdh/slide_page.html", ctx)
