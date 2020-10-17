from django.conf import settings
try:
    from django.contrib.sites.shortcuts import get_current_site as _get_current_site
    from django.contrib.sites.models import Site as SiteModel

    if getattr(settings, 'DJANGO_ATLASSIAN_CONNECT_ADDON', {}).get('use_sites_framework', False):
        def get_current_site(request=None):
            return _get_current_site(request)
    else:
        SiteModel = None

        def get_current_site(request=None):
            return None


except ImportError:
    SiteModel = None

    def get_current_site(request=None):
        return None
