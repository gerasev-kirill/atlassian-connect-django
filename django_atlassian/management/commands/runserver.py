from django.core.management.commands.runserver import Command as BaseCommand
from django_atlassian.addon import JiraAddon, ConfluenceAddon

import time, threading


class Command(BaseCommand):
    def get_handler(self, *args, **options):
        handler = super(Command, self).get_handler(*args, **options)

        def register_addon():
            time.sleep(0.4)
            jira_addon = JiraAddon()
            confluence_addon = ConfluenceAddon()
            jira_addon.register(port=self.port)
            confluence_addon.register(port=self.port)

        th = threading.Thread(target=register_addon, name='RegisterAddon')
        th.start()
        return handler
