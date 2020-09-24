# -*- coding: utf-8 -*-


import logging
import atlassian_jwt
import jwt

from django.utils.deprecation import MiddlewareMixin
from django.db import connections
from django.db.utils import ConnectionDoesNotExist
from django.conf import settings

from atlassian_connect_django.models.connect import SecurityContext, AtlassianUser
#import threading
#from django.apps import apps
#from atlassian_connect_django.models.djira import create_model
#lock = threading.Lock()

logger = logging.getLogger('atlassian_connect_django')




class DjangoAtlassianAuthenticator(atlassian_jwt.Authenticator):
    def get_shared_secret(self, client_key):
        sc = SecurityContext.objects.filter(client_key=client_key).get()
        return sc.shared_secret

    def get_atlassian_user(self, headers=None, query_params=None):
        token = self._get_token(headers=headers, query_params=query_params)
        if not token:
            return None
        data = jwt.decode(token, verify=False)
        '''
            from ACE:

          // Use the context.user if it exists. This is deprecated as per
          // https://ecosystem.atlassian.net/browse/AC-2424
          if (verifiedClaims.context) {
            verifiedParams.context = verifiedClaims.context;
            const user = verifiedClaims.context.user;
            if (user) {
              if (user.accountId) {
                verifiedParams.userAccountId = user.accountId;
              }
              if (user.userKey) {
                verifiedParams.userKey = user.userKey;
              }
            }
          }

          if (!verifiedParams.userAccountId) {
            // Otherwise use the sub claim, and assume it to be the AAID.
            // It will not be the AAID if they haven't opted in / if its before
            // the end of the deprecation period, but in that case context.user
            // will be used instead.
            verifiedParams.userAccountId = verifiedClaims.sub;
          }
        '''
        user_data = {}
        if 'context' in data and 'user' in data['context']:
            user_data = data['context']['user'] or {}
        if not user_data.get('userAccountId', None):
            user_data['userAccountId'] = data.get('sub', None)
        return AtlassianUser(**user_data)




class JWTAuthenticationMiddleware(MiddlewareMixin):
    def get_atlassian_data_from_request(self, request):
        if hasattr(request, 'atlassian_security_context') \
                and hasattr(request, 'atlassian_db') and hasattr(request, 'atlassian_user'):
            return request.atlassian_user, request.atlassian_security_context, request.atlassian_db
        headers = {}
        query = ''
        if request.method == 'POST':
            headers['Authorization'] = request.META.get('HTTP_AUTHORIZATION', None)
        # Generate the query
        params = []
        for key in list(request.GET.keys()):
            params.append("%s=%s" % (key, request.GET.get(key, None)))
        query = "&".join(params)

        auth = DjangoAtlassianAuthenticator()
        uri = request.path
        if query:
            uri = "%s?%s" % (uri, query)
        try:
            client_key = auth.authenticate(request.method, uri, headers)
        except Exception:
            if 'atlassian_connect_django.rest_framework' not in settings.INSTALLED_APPS:
                return AtlassianUser(), None, None
            client_key = None

        if not client_key:
            from atlassian_connect_django.rest_framework.authentication import get_atlassian_security_context_and_user_from_request as gadfr
            sc, user = gadfr(request)
            if not sc or not user:
                return AtlassianUser(), None, None
            client_key = sc.client_key
        else:
            sc = SecurityContext.objects.filter(client_key=client_key).get()
            user = auth.get_atlassian_user(headers=headers, query_params=request.GET)
            user.set_secutiry_context(security_context=sc)
        # Setup the request attributes, the security context and the model
        try:
            db = connections[client_key]
        except ConnectionDoesNotExist:
            connections.databases[client_key] = self._create_database(client_key, sc)
            db = connections[client_key]
        '''
        with lock:
            try:
                model = apps.get_model('atlassian_connect_django', client_key)
            except LookupError:
                logger.info("Model %s not found, creating it", str(client_key))
                model = create_model(str(client_key))
        '''
        return user, sc, db


    def process_request(self, request):
        request.atlassian_user, request.atlassian_security_context, request.atlassian_db = self.get_atlassian_data_from_request(request)
        return None


    def _create_database(self, name, sc):
        new_db = {}
        new_db['id'] = name
        new_db['ENGINE'] = 'atlassian_connect_django.backends.jira'
        new_db['NAME'] = sc.host
        new_db['USER'] = ''
        new_db['PASSWORD'] = ''
        new_db['HOST'] = ''
        new_db['PORT'] = ''
        new_db['SECURITY'] = sc
        return new_db
