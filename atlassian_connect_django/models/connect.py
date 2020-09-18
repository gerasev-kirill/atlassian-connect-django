# -*- coding: utf-8 -*-

import atlassian_jwt
import datetime, json
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

class SecurityContext(models.base.Model):
    """
    Stores the security context shared on the installation
    handshake process
    """

    shared_secret = models.CharField(max_length=512, null=False, blank=False)
    key = models.CharField(max_length=512, null=False, blank=False)
    client_key = models.CharField(max_length=512, null=False, blank=False)
    host = models.CharField(max_length=512, null=False, blank=False)
    is_plugin_enabled = models.BooleanField(default=True)


    def create_token(self, method, uri):
        token = atlassian_jwt.encode_token(method, uri, self.key, self.shared_secret)
        return token


    def __unicode__(self):
        return "%s: %s" % (self.key, self.host)




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
            if not k.startswith('__'):
                data[k] = getattr(self, k)
        return json.dumps(data, sort_keys=True, cls=DjangoJSONEncoder, ensure_ascii=False)

    def __str__(self):
        return self.__unicode__()
