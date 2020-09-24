# -*- coding: utf-8 -*-

import datetime, json
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from urllib.parse import urlparse
from atlassian_connect_django.requests import AtlassianRequest


try:
    import pytz
    def string_to_timezone(tz):
        try:
            return pytz.timezone(tz)
        except pytz.exceptions.UnknownTimeZoneError:
            return pytz.UTC
except ImportError:
    def string_to_timezone(tz):
        return tz






class SecurityContext(models.base.Model):
    """
    Stores the security context shared on the installation
    handshake process
    """

    shared_secret = models.CharField(max_length=512, null=False, blank=False)
    key = models.CharField(max_length=512, null=False, blank=False)
    client_key = models.CharField(max_length=512, null=False, blank=False)
    host = models.CharField(max_length=512, null=False, blank=False)
    oauth_client_id = models.CharField(max_length=512, null=False, blank=False)
    is_plugin_enabled = models.BooleanField(default=True)

    def get_requests(self, as_atlassian_user_account_id=None):
        return AtlassianRequest(security_context=self, as_atlassian_user_account_id=as_atlassian_user_account_id)

    def __unicode__(self):
        return "%s: %s" % (self.key, self.host)








class AtlassianUser(object):
    accountId = None
    _security_context = None

    def __init__(self, **kwargs):
        for k in kwargs:
            if k == 'userAccountId':
                setattr(self, 'accountId', kwargs[k])
            else:
                setattr(self, k, kwargs[k])

    def is_authenticated(self):
        return bool(self.accountId)

    def set_secutiry_context(self, security_context=None):
        self._security_context = security_context

    def refresh_from_db(self, using=None, fields=None):
        if not self._security_context or not self.is_authenticated():
            return
        data = self._security_context.get_requests(as_atlassian_user_account_id=self.accountId).get(
            "/rest/api/3/myself"
        )
        for k,v in data.items():
            if k == 'timeZone':
                v = string_to_timezone(v)
            setattr(self, k, v)

    def get_requests(self):
        if not self._security_context:
            raise Exception("Provide security context with set_secutiry_context function")
        if not self.is_authenticated():
            raise Exception("User is not authenticated!")
        return self._security_context.get_requests(as_atlassian_user_account_id=self.accountId)

    def __unicode__(self):
        if self.is_authenticated():
            return "<Atlassian user: %s>" % self.accountId
        return "<Anonymous atlassian user>"

    def __str__(self):
        return self.__unicode__()





def detect_host(payload):
    for k,v in payload.items():
        if k == 'self' and isinstance(v, str) and v.startswith('https://'):
            parsed_uri = urlparse(v)
            return '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
        if isinstance(v, dict):
            return detect_host(v)
    return None


class WebhookPayload(object):
    def __init__(self, **kwargs):
        for k in kwargs:
            if k == 'timestamp':
                dt = datetime.datetime.fromtimestamp(kwargs[k] / 1e3)
                dt.replace(tzinfo=datetime.timezone.utc)
                setattr(self, k, dt)
            else:
                setattr(self, k, kwargs[k])

    def __unicode__(self):
        data = {}
        for k in dir(self):
            v = getattr(self, k)
            if not k.startswith('__') and not callable(v):
                data[k] = v
        return json.dumps(data, sort_keys=True, cls=DjangoJSONEncoder, ensure_ascii=False)

    def __str__(self):
        return self.__unicode__()

    def get_host(self):
        for k in dir(self):
            v = getattr(self, k)
            if not k.startswith('__') and isinstance(v, dict):
                host = detect_host(v)
                if host:
                    return host
        return None

    def __iter__(self):
        for k in dir(self):
            v = getattr(self, k)
            if not k.startswith('__') and not callable(v):
                yield k,v
