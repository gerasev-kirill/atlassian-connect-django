# -*- coding: utf-8 -*-


from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^installed/$', views.LifecycleInstalledView.as_view(), name='atlassian-connect-django-installed'),
    url(r'^enabled/$', views.LifecycleEnabledView.as_view(), name='atlassian-connect-django-enabled'),
    url(r'^disabled/$', views.LifecycleDisabledView.as_view(), name='atlassian-connect-django-disabled'),
    url(r'^uninstalled/$', views.LifecycleUninstalledView.as_view(), name='atlassian-connect-django-uninstalled'),
    url(r'^webhooks/(?P<webhook_name>[\w\-]+)/$', views.WebhookView.as_view(), name='atlassian-connect-django-webhook'),
    url(r'^jira/atlassian-connect.json$', views.JiraDescriptor.as_view(), name='atlassian-connect-django-jira-connect-json'),
    url(r'^confluence/atlassian-connect.json$', views.ConfluenceDescriptor.as_view(), name='atlassian-connect-django-confluence-connect-json'),
]
