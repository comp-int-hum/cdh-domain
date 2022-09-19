from rest_framework.negotiation import DefaultContentNegotiation


class CdhContentNegotiation(DefaultContentNegotiation):

    def select_renderer(self, request, renderers, format_suffix):
        if "include=true" in request.headers.get("Accept", "") or request.headers.get("include"):
            return (renderers[-1], renderers[-1].media_type)
        else:
            return super(CdhContentNegotiation, self).select_renderer(request, renderers, format_suffix)
