
import requests
import jwt
import atlassian_jwt
from django.core.exceptions import ImproperlyConfigured
from time import time
from urllib.parse import urljoin, urlparse, parse_qs, urlencode
from atlassian_connect_django.models.cache import AtlassianUserOAuth2BearerToken



class FakeRequestsResponse(object):
    _json = None
    def __init__(self, json={}, status_code=200):
        self._json = json
        self.status_code = 200

    def json(self):
        return self._json


def get_query_value(query, k):
    if k not in query:
        return None
    if isinstance(query.get(k, None), list):
        if len(query[k]) > 0:
            return query[k][0]
        return None
    return query[k]





# https://bitbucket.org/atlassian/atlassian-oauth2-js/src/master/lib/oauth2.js
class AtlassianOAuth2:
    EXPIRE_IN_SECONDS = 60
    AUTHORIZATION_SERVER_URL = "https://oauth-2-authorization-server.services.atlassian.com"
    JWT_CLAIM_PREFIX = "urn:atlassian:connect"
    GRANT_TYPE = "urn:ietf:params:oauth:grant-type:jwt-bearer",
    SCOPE_SEPARATOR = ' '
    _security_context = None
    _last_cache = None
    '''

    * @param {String} host - The fully qualified instance name, for example `https://instance.atlassian.net`
    * @param {String} oauth_client_id - The OAuth client id which corresponds to the `hostBaseUrl` which was provided to the add-on during installation
    '''
    def __init__(self, security_context):
        self._security_context = security_context

    def update_security_context(self, security_context=None):
        if security_context != self._security_context:
            self._last_cache = None
        self._security_context = security_context

    def _get_user_token_from_cache(self, atlassian_user_id):
        if not self._last_cache:
            self._last_cache, creater = AtlassianUserOAuth2BearerToken.objects.get_or_create(account_id=atlassian_user_id)
        else:
            self._last_cache.refresh_from_db(fields=['token_cache'])
        return self._last_cache.get_token_from_cache(self._security_context)

    def _add_user_token_to_cache(self, atlassian_user_id, response):
        if not self._last_cache or self._last_cache.account_id != atlassian_user_id:
            self._last_cache, creater = AtlassianUserOAuth2BearerToken.objects.get_or_create(account_id=atlassian_user_id)
        self._last_cache.add_token_to_cache(self._security_context, response['access_token'], expires_in=response['expires_in'])

    '''
     * Creates a JWT claimset for authenticating the add-on to the OAuth2 service.
     *
     * This is the generic base used to generate payloads for both accountId and userKey.
     *
     * @param {String} subClaim - The sub claim to use when making the request to the server.
     * @param {String=} audience - The authorization server to use (only intended to be changed for internal Atlassian use).
     * @returns {Object} A claimset to be encoded and sent with the token request
    '''
    def create_generic_assertion_payload(self, subClaim, audience=None):
        # https://developer.atlassian.com/cloud/jira/platform/user-impersonation-for-connect-apps/
        now = int(time())
        exp = now + self.EXPIRE_IN_SECONDS
        return {
            "iss": self.JWT_CLAIM_PREFIX + ":clientid:" + self._security_context.oauth_client_id,
            "tnt": self._security_context.host,
            "sub": subClaim,
            "aud": audience or self.AUTHORIZATION_SERVER_URL,
            "iat": now,
            "exp": exp
        }

    def create_AAID_asserting_payload(self, aAID, audience=None):
        subClaim = self.JWT_CLAIM_PREFIX + ":useraccountid:" + aAID
        return self.create_generic_assertion_payload(subClaim, audience=audience)

    '''
     * Retrieves an OAuth 2 access token for a given user and instance by creating a JWT token
     * signed by the add-on's shared secret.
     *
     * @param {String} scopes - An array of scopes to request for when creating the access token
    '''
    def get_access_token(self, atlassian_user_account_id, scopes=None):
        if not atlassian_user_account_id:
            raise ImproperlyConfigured("No user identifier (atlassian_user_account_id) provided!")
        user_token = self._get_user_token_from_cache(atlassian_user_id=atlassian_user_account_id)
        if user_token:
            return user_token
        jwtClaims = self.create_AAID_asserting_payload(atlassian_user_account_id)
        assertion = jwt.encode(key=self._security_context.shared_secret, algorithm='HS256', payload=jwtClaims).decode('utf8')
        formData = {
            'grant_type': self.GRANT_TYPE,
            'assertion': assertion
        }
        if scopes:
            formData['scope'] = self.SCOPE_SEPARATOR.join(scopes).upper()

        response = requests.post(
            self.AUTHORIZATION_SERVER_URL + '/oauth2/token',
            data=formData,
            headers={
                'Accept': 'application/json'
            }
        )
        if response.status_code != 200:
            try:
                data = response.json()
            except:
                data = response.text
            raise ImproperlyConfigured("Failed to fetch token for OAuth2: %s" % data)

        r = response.json()
        self._add_user_token_to_cache(atlassian_user_account_id, r)
        print('GOT TOKEN', r['access_token'])
        return r['access_token']




class AtlassianRequest(object):
    _oauth2 = None
    def __init__(self, security_context=None, as_atlassian_user_account_id=None):
        self._security_context = security_context
        self._request = requests.Session()
        self._as_atlassian_user_account_id = as_atlassian_user_account_id


    def _create_auth_header(self, method, url):
        if not self._as_atlassian_user_account_id:
            return "JWT %s" % atlassian_jwt.encode_token(method.upper(), url, self._security_context.key, self._security_context.shared_secret)

        if not self._security_context.oauth_client_id:
            raise ImproperlyConfigured("This security context doesn't have 'ACT_AS_USER' permission in scope! You can't run create_auth_header method as user!")
        if not self._oauth2:
            self._oauth2 = AtlassianOAuth2(self._security_context)
        return "Bearer %s" % self._oauth2.get_access_token(self._as_atlassian_user_account_id)


    def _base(self, method, url, *args, **kwargs):
        requests_method = getattr(self._request, method)
        url = urljoin(self._security_context.host, url)
        url_parsed = urlparse(url)
        query = parse_qs(url_parsed.query or '')
        kwargs['headers'] = kwargs.get('headers', None) or {}

        if get_query_value(query, 'maxResults') != 'ALL':
            kwargs['headers']['Authorization'] = self._create_auth_header(method, url)
            response = requests_method(url, *args, **kwargs)
            print(response.__dict__)
            return response

        # загружаем все результаты из paginated ответа джиры
        result = []
        resultName = None
        baseUrl = url.split('?')[0]
        startAt = 0
        maxResults = 50
        # очищаем параметры от синтаксического сахара
        queryCleaned = {}
        for k,v in query.items():
            if k == 'startAt':
                v = get_query_value(query, k)
                startAt = v
            if k != 'maxResults':
                queryCleaned[k] = v

        queryCleaned['startAt'] = None
        queryCleaned['maxResults'] = None

        def load_items(_startAt, _maxResults):
            queryCleaned['startAt'] = _startAt
            queryCleaned['maxResults'] = _maxResults
            url_paginated = baseUrl + '?' + urlencode(queryCleaned)
            kwargs['headers']['Authorization'] = self._create_auth_header(method, url_paginated)
            response = requests_method(url_paginated, *args, **kwargs)
            if response.status_code not in [200, 201]:
                return response
            responseJson = response.json()
            # аккуратно мерджим объекты избегая дублей
            for prop,items in responseJson.items():
                if isinstance(items, list):
                    resultName = prop
                    for item in items:
                        exists = next((x for x in result if x['id'] == item['id']), None)
                        if not exists:
                            result.append(item)
                    break
            '''
                согласно докам:
                maxResults is the maximum number of items that can be returned per page.
                Each API endpoint may have a different limit for the number of
                items returned, and these limits may change without notice.
            '''
            maxItemsCount = _startAt + _maxResults
            if responseJson.get('isLast', None) or ('total' in responseJson and responseJson['total'] <= maxItemsCount):
                # возвращаем объект
                responseJson['startAt'] = startAt
                responseJson['maxResults'] = len(result)
                responseJson['total'] = responseJson['maxResults']
                responseJson[resultName] = result
                return FakeRequestsResponse(json=responseJson)
            # продолжаем загрузку
            return load_items(_startAt + responseJson.get('maxResults', 0), responseJson.get('maxResults', 0))

        return load_items(startAt, maxResults)

    def get(self, url, *args, **kwargs):
        return self._base('get', url, *args, **kwargs)
    def post(self, url, *args, **kwargs):
        return self._base('post', url, *args, **kwargs)
    def put(self, url, *args, **kwargs):
        return self._base('put', url, *args, **kwargs)
    def patch(self, url, *args, **kwargs):
        return self._base('patch', url, *args, **kwargs)
    def delete(self, url, *args, **kwargs):
        return self._base('delete', url, *args, **kwargs)
