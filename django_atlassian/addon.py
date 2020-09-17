# -*- coding: utf-8 -*-
import json, os, jsmin, logging, atexit, requests, time
from urllib.parse import urlparse, urljoin
from django.conf import settings
from django.urls import reverse
from . import signals

logger = logging.getLogger('django_atlassian')
ngrok_url_by_ports = {}


def read_json_file(filepath):
    if not os.path.exists(os.path.join(settings.BASE_DIR, filepath)):
        return {}
    with open(os.path.join(settings.BASE_DIR, filepath)) as js_file:
        data = js_file.read()
        try:
            data = jsmin.jsmin(data)
        except:
            pass
        data = json.loads(data)
    return data or {}


def create_ngrok_tunnel(port=None):
    from pyngrok import ngrok

    if port is None:
        port = 80
    if port not in ngrok_url_by_ports:
        ltu = urlparse(ngrok.connect(port=port))
        lbu = urlparse(
            os.environ.get('AC_LOCAL_BASE_URL', None) or 'http://localhost:8000'
        )
        lbu = lbu._replace(scheme='https')
        lbu = lbu._replace(netloc=ltu.netloc)
        ngrok_url_by_ports[port] = lbu.geturl()
        #os.environ.setdefault('AC_LOCAL_BASE_URL', public_url)
    return ngrok_url_by_ports[port]


def get_error(request):
    try:
        return request.json()
    except:
        pass
    return request.content




class BaseAddon(object):
    product = None
    is_dev_mode = True
    is_registered = False
    local_base_url = None

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(BaseAddon, cls).__new__(cls)
        return cls.instance

    def __init__(self, **kwargs):
        if os.environ.get('NODE_ENV', None) == 'production' or not settings.DEBUG:
            self.is_dev_mode = False
        atexit.register(self.unregister)


    def get_local_base_url(self, request=None):
        if not request or self.is_dev_mode:
            return self.local_base_url
        if request:
            return request.build_absolute_uri('/')[:-1]
        return ''


    def get_hosts_for_plugin(self):
        credentials = read_json_file('credentials.json')
        hosts = {}
        for host, auth_data in (credentials.get('hosts', None) or {}).items():
            if auth_data and auth_data.get('product', None) == self.product:
                hosts[host] = auth_data
        return hosts


    def register(self, port=None):
        ac_opts = os.environ.get('AC_OPTS', None) or ''
        if 'no-reg' in ac_opts:
            logger.warn("Auto-registration disabled with AC_OPTS=no-reg")
            return

        atexit.unregister(self.unregister)
        atexit.register(self.unregister)

        if not self.is_dev_mode and 'force-reg' not in ac_opts:
            return

        hosts = self.get_hosts_for_plugin()
        if not hosts:
            logger.warn("Add-on not registered; no compatible hosts detected. Provide them in credentials.json")
            return

        self.local_base_url = create_ngrok_tunnel(port=port)
        self.is_registered = False
        descriptor_url = urljoin(
            self.local_base_url,
            reverse('django-atlassian-jira-connect-json')
        )
        signals.localtunnel_started.send(sender=self.__class__)

        def wait_for_registration_result(host, auth_data, json_data, timeout=0):
            if timeout > 30:
                return False, "Add-on installation timed out"
            r = requests.get(
                urljoin(host, json_data['links']['self']),
                auth=(auth_data['username'], auth_data['password'])
            )
            if r.status_code < 200 or r.status_code > 299:
                return False, get_error(r)

            results = r.json()
            # UPM installed payload changes on successful install
            if results.get('status', None) and results['status'].get('done', False):
                # if results.status.done is true, then the build has failed as the payload of a
                # successful install does not contain the status object
                error = results['status'].get('errorMessage', None) or results['status'].get('subCode', None)
                return False, "Unable to install addon on %s. Error: %s" % (host, error)
            elif results.get('key', None):
                # Key will only exist if the install succeeds
                return True, None
            time.sleep(0.1)
            return wait_for_registration_result(host, auth_data, results, timeout+0.1)



        for host,auth_data in hosts.items():
            session = requests.Session()
            r = session.get(
                urljoin(host, "/rest/plugins/1.0/"),
                auth=(auth_data['username'], auth_data['password'])
            )
            if r.status_code < 200 or r.status_code > 299:
                logger.error("%s: Invalid username or passworn on %s. Error: %s" % (self.product.upper(), host, get_error(r)))
                continue

            r_addon = session.post(
                urljoin(host, "/rest/plugins/1.0/"),
                params={'token': r.headers['upm-token']},
                headers={
                    'content-type': 'application/vnd.atl.plugins.remote.install+json',
                },
                auth=(auth_data['username'], auth_data['password']),
                data=json.dumps({'pluginUri': descriptor_url})
            )
            if r_addon.status_code != 202:
                logger.error("%s: Unable to install addon on %s. Error: %s" % (self.product.upper(), host, get_error(r_addon)))
                continue

            is_installed, message = wait_for_registration_result(host, auth_data, r_addon.json())
            if is_installed:
                logger.warn("%s: ✅ Add-on is installed on %s" % (self.product.upper(), host))
                self.is_registered = True
                signals.addon_registered.send(sender=self.__class__)
            else:
                message = message or "Unable to install add-on on %s" % host
                logger.warn("%s: ❌ %s" % (self.product.upper(), message))


    def unregister(self):
        atexit.unregister(self.unregister)
        if not self.is_registered:
            return
        ac_opts = os.environ.get('AC_OPTS', None) or ''
        if 'no-reg' in ac_opts:
            logger.warn("%s: Auto-deregistration disabled with AC_OPTS=no-reg" % self.product.upper())
            return
        if not self.is_dev_mode and 'force-dereg' not in ac_opts:
            return

        hosts = self.get_hosts_for_plugin()
        plugin_key = getattr(settings, 'DJANGO_ATLASSIAN_CONNECT_ADDON_{}'.format(self.product.upper()))['pluginKey']
        if not hosts:
            return

        for host,auth_data in hosts.items():
            session = requests.Session()
            r_addon = session.delete(
                urljoin(host, "/rest/plugins/1.0/%s-key" % plugin_key),
                auth=(auth_data['username'], auth_data['password'])
            )
            if r_addon.status_code < 200 or r_addon.status_code > 299:
                logger.warn("%s: Unable to uninstall add-on on %s" % (host, self.product.upper()))
                continue
            self.is_registered = False
            signals.addon_deregistered.send(sender=self.__class__)




class JiraAddon(BaseAddon):
    product = 'jira'



class ConfluenceAddon(BaseAddon):
    product = 'confluence'

    def register(self, port=None):
        logger.warn("%s: 🤔 register is not implemented" % self.product.upper())

    def unregister(self, port=None):
        if not self.is_registered:
            return
        logger.warn("%s: 🤔 unregister is not implemented" % self.product.upper())
