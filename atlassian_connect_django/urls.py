try:
    from django.urls import re_path
except:
    # DEPRECATED: django < 2.0
    from django.conf.urls import url as re_path

from . import views

urlpatterns = [
    re_path(r'^installed/$', views.LifecycleInstalledView.as_view(), name='atlassian-connect-django-installed'),
    re_path(r'^enabled/$', views.LifecycleEnabledView.as_view(), name='atlassian-connect-django-enabled'),
    re_path(r'^disabled/$', views.LifecycleDisabledView.as_view(), name='atlassian-connect-django-disabled'),
    re_path(r'^uninstalled/$', views.LifecycleUninstalledView.as_view(), name='atlassian-connect-django-uninstalled'),
    re_path(r'^webhooks/(?P<webhook_name>[:\/\.\w]+)/$', views.WebhookView.as_view(), name='atlassian-connect-django-webhook'),
    re_path(r'^jira/atlassian-connect.json$', views.JiraDescriptor.as_view(), name='atlassian-connect-django-jira-connect-json'),
    re_path(r'^confluence/atlassian-connect.json$', views.ConfluenceDescriptor.as_view(), name='atlassian-connect-django-confluence-connect-json'),
]
