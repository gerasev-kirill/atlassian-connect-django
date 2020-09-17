# -*- coding: utf-8 -*-


from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^installed/$', views.LifecycleInstalledView.as_view(), name='django-atlassian-installed'),
    url(r'^uninstalled/$', views.LifecycleUninstalledView.as_view(), name='django-atlassian-uninstalled'),
    url(r'^jira/atlassian-connect.json$', views.JiraDescriptor.as_view(), name='django-atlassian-jira-connect-json'),
    url(r'^confluence/atlassian-connect.json$', views.ConfluenceDescriptor.as_view(), name='django-atlassian-confluence-connect-json'),
]
