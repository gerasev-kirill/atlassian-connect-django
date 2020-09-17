# -*- coding: utf-8 -*-


from importlib import import_module
import json, six

from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.apps import apps
from django.views.generic.base import TemplateView
from django.views import View
from django.core.exceptions import ImproperlyConfigured

from .models.connect import SecurityContext, WebhookPayload
from .addon import JiraAddon, ConfluenceAddon, BaseAddon
from .decorators import jwt_required

from . import signals


@method_decorator(csrf_exempt, name='dispatch')
class LifecycleView(View):
    def get_payload_from_request(self, request):
        try:
            body_unicode = request.body
            if not six.PY2:
                body_unicode = body_unicode.decode('utf-8')
            post = json.loads(body_unicode)
            return {
                'key': post['key'],
                'sharedSecret': post.get('sharedSecret', None),
                'clientKey': post['clientKey'],
                'host': post['baseUrl'],
                'product': post['productType']
            }
        except MultiValueDictKeyError:
            return None

    def get_addon_class_from_payload(self, payload=None):
        if not payload or not payload.get('product', None):
            return BaseAddon
        if payload['product'] == 'jira':
            return JiraAddon
        if payload['product'] == 'confluence':
            return ConfluenceAddon
        return BaseAddon



class LifecycleInstalledView(LifecycleView):
    def post(self, request, *args, **kwargs):
        payload = self.get_payload_from_request(request)
        addon_class = self.get_addon_class_from_payload(payload)

        if not payload:
            signals.host_settings_not_saved.send(sender=addon_class, payload=None)
            return HttpResponseBadRequest()
        # Store the security context
        # https://developer.atlassian.com/cloud/jira/platform/authentication-for-apps/
        sc = SecurityContext.objects.filter(key=payload['key'], host=payload['host']).first()
        if sc:
            update = False
            # Confirm that the shared key is the same, otherwise update it
            if sc.shared_secret != payload['sharedSecret']:
                sc.shared_secret = payload['sharedSecret']
                update = True
            if sc.client_key != payload['clientKey']:
                sc.client_key = payload['clientKey']
                update = True
            if update:
                try:
                    sc.save()
                    signals.host_settings_saved.send(sender=addon_class, payload=payload, security_context=sc)
                except Exception as e:
                    signals.host_settings_not_saved.send(sender=addon_class, payload=payload, security_context=sc, exception=e)
        else:
            # Create a new entry on our database of connections
            sc = SecurityContext(
                key=payload['key'],
                host=payload['host'],
                shared_secret=payload['sharedSecret'],
                client_key=payload['clientKey']
            )
            try:
                sc.save()
                signals.host_settings_saved.send(sender=addon_class, payload=payload, security_context=sc)
            except Exception as e:
                signals.host_settings_not_saved.send(sender=addon_class, payload=payload, security_context=sc, exception=e)

        return HttpResponse(status=204)




class LifecycleUninstalledView(LifecycleView):
    def post(self, request, *args, **kwargs):
        payload = self.get_payload_from_request(request)
        addon_class = self.get_addon_class_from_payload(payload)

        if not payload:
            signals.host_settings_not_saved.send(sender=addon_class, payload=None)
            return HttpResponseBadRequest()
        return HttpResponse(status=204)




@method_decorator(jwt_required, name='dispatch')
@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View):
    def get_payload_from_request(self, request):
        try:
            body_unicode = request.body
            if not six.PY2:
                body_unicode = body_unicode.decode('utf-8')
            return json.loads(body_unicode)
        except:
            return None


    def post(self, request, *args, **kwargs):
        payload = self.get_payload_from_request(request)
        if not payload:
            return HttpResponseBadRequest()
        signals.webhook_auth_verification_successful.send(
            sender=BaseAddon,
            payload_obj=WebhookPayload(**payload), 
            webhook_name=kwargs['webhook_name']
        )
        return HttpResponse(status=204)





class ApplicationDescriptor(TemplateView):
    content_type = 'application/json'

    def get_application_name(self):
        if self.application_name is None:
            raise ImproperlyConfigured(
                "ApplicationDescriptor requires a definition of 'application_name' "
                "or an implementation of 'get_application_name()'")
        return self.application_name

    def get_template_names(self):
        return ['django_atlassian/{}/atlassian-connect.json'.format(self.get_application_name())]

    def get_context_data(self, *args, **kwargs):
        if self.application_name == 'jira':
            addon = JiraAddon()
        elif self.application_name == 'confluence':
            addon = ConfluenceAddon()
        else:
            raise NameError("Unknown application name '%s'" % self.application_name)

        context = super(ApplicationDescriptor, self).get_context_data(*args, **kwargs)
        context['localBaseUrl'] = addon.get_local_base_url(self.request)
        # Get the needed settings or abort
        prop = 'DJANGO_ATLASSIAN_CONNECT_ADDON_{}'.format(self.get_application_name().upper())
        config = {}
        if hasattr(settings, prop):
            config = (getattr(settings, prop) or {}).copy()
        config['vendorName'] = config.get('vendorName', None) or 'Test, Inc.'
        config['vendorUrl'] = config.get('vendorUrl', None) or context['localBaseUrl']
        context.update(config)
        # Get all the contents of the registered apps {jira|confluence}_atlassian_connect.py files
        for app in apps.get_app_configs():
            try:
                module = import_module('{}.{}_atlassian_connect'.format(app.module.__name__, self.get_application_name()))
            except ImportError:
                continue
            if not hasattr(module, 'get_connect_data') or not callable(module.get_connect_data):
                continue
            connect_data = module.get_connect_data(request=self.request, addon=addon)
            context.update(connect_data)

        context = addon.normalize_addon_connect_config(context)
        context['modules'] = json.dumps(context.get('modules', None) or {})
        if 'pluginScopes' in context and not isinstance(context['pluginScopes'], str):
            context['pluginScopes'] = json.dumps(context['pluginScopes'])
        return context


class JiraDescriptor(ApplicationDescriptor):
    application_name = 'jira'


class ConfluenceDescriptor(ApplicationDescriptor):
    application_name = 'confluence'
