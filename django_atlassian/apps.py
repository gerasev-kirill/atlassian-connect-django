# -*- coding: utf-8 -*-


from django.apps import AppConfig


class DjangoAtlassianConfig(AppConfig):
    name = 'django_atlassian'
    verbose_name = 'Atlassian connector for django'

    def ready(self):
        from .addon import JiraAddon, ConfluenceAddon
        jira_addon = JiraAddon()
        confluence_addon = ConfluenceAddon()
