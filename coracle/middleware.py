from django.urls import set_urlconf


class CoracleUrlconfMiddleware:
    """Override pretix's urlconf with coracle's.

    Pretix's MultiDomainMiddleware sets request.urlconf to its own URL config.
    This middleware runs immediately after and overrides it with coracle's URLs.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.urlconf = 'coracle.urls'
        set_urlconf('coracle.urls')
        return self.get_response(request)
