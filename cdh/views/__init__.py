from django.urls import path
from django.db.models.base import ModelBase
from .cache import cdh_cache_method, cdh_cache_function
from .mixins import NestedMixin, ButtonsMixin
from .select import SelectView
from .permissions import PermissionsView
from .slides import SlidesView
from .markdown import MarkdownView
from .sparql import SparqlView
from .material import MaterialView
