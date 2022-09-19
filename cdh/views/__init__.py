from django.urls import path
from django.db.models.base import ModelBase
from .cache import cdh_cache_method, cdh_cache_function
from .mixins import NestedMixin, ButtonsMixin
from .atomic import AtomicView
from .accordion import AccordionView
from .tabs import TabsView
from .vega import VegaView
from .select import SelectView
from .permissions import PermissionsView
from .slides import SlidesView
from .markdown import MarkdownView
from .sparql import SparqlView
from .material import MaterialView

def generate_default_urls(*items):
    urls = []
    for item in items:
        model = item if isinstance(item, ModelBase) else item[0]
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        urls += [
            path(
                '{}/<int:pk>/'.format(model_name),
                AtomicView.as_view(
                    model=model,
                    fields="__all__",
                ),
                name="{}_detail".format(model_name)
            ),
            path(
                '{}/<int:pk>/edit/'.format(model_name),
                AtomicView.as_view(
                    model=model,
                    editable=True,
                    fields="__all__",
                ),
                name="{}_edit".format(model_name)
            ),
            path(
                '{}/create/'.format(model_name),
                AtomicView.as_view(
                    model=model,
                    editable=True,
                    can_update=True,
                    fields="__all__",
                ),
                name="{}_create".format(model_name)
            ),
            path(
                '{}/list/'.format(model_name),
                AccordionView.as_view(
                    model=model,
                ),
                name="{}_list".format(model_name)
            ),
            path(
                '{}/<int:pk>/'.format(model_name),
                AtomicView.as_view(
                    model=model,
                    fields="__all__",
                    can_delete=True,
                    can_update=False,
                    can_create=False,
                    can_manage=False
                ),
                name="{}_delete".format(model_name)
            ),            
        ]
    return urls
