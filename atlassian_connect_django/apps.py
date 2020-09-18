# -*- coding: utf-8 -*-


from django.apps import AppConfig


class DjangoAtlassianConfig(AppConfig):
    name = 'atlassian_connect_django'
    verbose_name = 'Atlassian connector for django'

    def ready(self):
        from .addon import JiraAddon, ConfluenceAddon
        jira_addon = JiraAddon()
        confluence_addon = ConfluenceAddon()
