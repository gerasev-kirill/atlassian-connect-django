
from time import time
from django.db import models


try:
    from django.db.models import JSONField as BaseJSONField
    class JSONField(BaseJSONField):
        def __init__(self, *args, **kwargs):
            kwargs['default'] = dict
            super(JSONField, self).__init__(*args, **kwargs)
except ImportError:
    from jsonfield import JSONField as BaseJSONField
    class JSONField(BaseJSONField):
        def __init__(self, *args, **kwargs):
            kwargs['default'] = {}
            super(JSONField, self).__init__(*args, **kwargs)




class AtlassianUserOAuth2BearerToken(models.base.Model):
    account_id = models.CharField(max_length=512, primary_key=True)
    token_cache = JSONField()

    def get_token_from_cache(self, security_context):
        id = str(security_context.id)
        if id not in self.token_cache:
            return None
        now = int(time())
        if self.token_cache[id]['expires'] > now + 10:
            print('GOT TOKEN from cache!', self.token_cache[id]['expires'], now+10)
            return self.token_cache[id]['token']
        del self.token_cache[id]['token']
        self.save(update_fields=['token_cache'])
        return None

    def add_token_to_cache(self, security_context, token, expires_in=0):
        if not expires_in:
            return
        exptime = int(time()) + 10
        for id in list(self.token_cache.keys()):
            if self.token_cache[id]['expires'] > exptime:
                del self.token_cache[id]
        self.token_cache[str(security_context.id)] = {
            'expires': int(time()) + expires_in,
            'token': token
        }
        self.save(update_fields=['token_cache'])
