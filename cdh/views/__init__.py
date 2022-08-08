from django.shortcuts import render, get_object_or_404
from ..models import SlidePage, Slide, User
from .cache import cdh_cache_method, cdh_cache_function
from .mixins import NestedMixin, PermissionsMixin
from .base import BaseView
from .accordion import AccordionView
from .tabs import TabsView
from .vega import VegaView
from .select import SelectView


def slide_page(request, page):    
    context = {
        "page" : page,
        "slides" : page.slides.filter(active=True),
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
        ],
    }
    return render(request, 'cdh/slide_page.html', context)


def index(request):
    slidepages = SlidePage.objects.filter(name="news")    
    if len(slidepages) == 0:
        slidepage = SlidePage(name="news")
        slidepage.save()
    else:
        slidepage = slidepages[0]
    return slide_page(request, slidepage)


def slide_detail(request, sid):
    context = {
        "slide" : Slide.objects.get(id=sid)
    }
    return render(request, 'cdh/slide_detail.html', context)


def people(request):
    faculty = User.objects.filter(groups__name="faculty")
    postdocs = User.objects.filter(groups__name="postdoc")
    students = User.objects.filter(groups__name="student")
    affiliates = User.objects.filter(groups__name="affiliate")
    context = {
        "categories" : {
            "Faculty" : sorted(faculty, key=lambda x : x.last_name),
            "Post-doctoral fellows" : sorted(postdocs, key=lambda x : x.last_name),
            "Current and Past Students" : sorted(students, key=lambda x : x.last_name),
        }
    }
    return render(request, 'cdh/people.html', context)


def research(request):
    slidepages = SlidePage.objects.filter(name="research")
    if len(slidepages) == 0:
        slidepage = SlidePage(name="research")
        slidepage.save()
    else:
        slidepage = slidepages[0]
    return slide_page(request, slidepage)


def calendar(request):
   context = {
   }
   return render(request, 'cdh/calendar.html', context)


def about(request):
    context = {
    }
    return render(request, 'cdh/about.html', context)


