from six import text_type
from rest_framework import HTTP_HEADER_ENCODING, exceptions
from django.core.exceptions import PermissionDenied
try:
    # DEPRECATED
    from django.utils.translation import ugettext_lazy as _
except ImportError:
    # django >= 4.0.0
    from django.utils.translation import gettext_lazy as _

from atlassian_connect_django.models.connect import AtlassianUser
from atlassian_connect_django import helpers
from .models import SecurityContextToken








def get_atlassian_security_context_and_user_from_request(request, raise_exceptions=True):
    def exception(msg):
        if not raise_exceptions:
            return None, None
        if raise_exceptions == 'rest_framework':
            raise exceptions.AuthenticationFailed(msg)
        raise PermissionDenied(msg)

    auth = request.META.get('HTTP_X_JIRA_SECURITY_CONTEXT', b'')
    if isinstance(auth, text_type):
        # Work around django test client oddness
        auth = auth.encode(HTTP_HEADER_ENCODING)
    auth = auth.split()
    if not auth or auth[0].lower() != b'token':
        return None, None

    if len(auth) == 1:
        return exception(_('Invalid x-jira-security-context token header. No credentials provided.'))
    elif len(auth) > 2:
        return exception(_('Invalid x-jira-security-context token header. Token string should not contain spaces.'))
    try:
        token = auth[1].decode()
    except UnicodeError:
        return exception(_('Invalid x-jira-security-context token header. Token string should not contain invalid characters.'))

    try:
        token = SecurityContextToken.objects.select_related('security_context').get(key=token)
    except SecurityContextToken.DoesNotExist:
        return exception(_('Invalid x-jira-security-context token.'))
    if not token.security_context.is_plugin_enabled:
        return exception(_('Security context inactive or deleted.'))

    site = helpers.get_current_site(request=request)
    if site and site != token.security_context.site:
        return exception(_('Invalid x-jira-security-context token header. SecurityContext site "%s" not equals to "%s"' % (token.security_context.site.name, site.name)))
    atlassian_user = AtlassianUser(accountId=token.atlassian_user_account_id)
    atlassian_user.set_secutiry_context(security_context=token.security_context)
    return token.security_context, atlassian_user
