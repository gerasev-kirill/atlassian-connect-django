# -*- coding: utf-8 -*-


from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^installed/$', views.installed, name='django-atlassian-installed'),
    url(r'^jira/$', views.JiraDescriptor.as_view(), name='django-atlassian-jira-connect-json'),
    url(r'^confluence/$', views.ConfluenceDescriptor.as_view(), name='django-atlassian-confluence-connect-json'),
]
