import logging
from django.shortcuts import render, get_object_or_404
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin
from django.views import View
from django.utils.safestring import mark_safe
from cdh.widgets import VegaWidget
from cdh.views import AtomicView


logger = logging.getLogger("django")


class VegaView(AtomicView):
    """
    A VegaView renders a dynamic Vega visualization.  The as_view() method
    accepts the following arguments:

      preamble
      model
      model_attr
      vega_class    
    """
    template_name = "cdh/atomic.html"
    model = None
    vega_class = None
    model_attr = None
    preamble = None

    def get(self, request, *argv, **argd):
        ctx = self.get_context_data()
        ctx["content"] = VegaWidget(vega_class=self.vega_class).render("", getattr(self.get_object(), self.model_attr))
        return self.render_to_response(ctx)
