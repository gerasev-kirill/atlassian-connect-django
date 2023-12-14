from atlassian_connect_django.addon import JiraAddon, ConfluenceAddon
from django.conf import settings
import time, threading


if 'channels' in settings.INSTALLED_APPS and getattr(settings, 'ASGI_APPLICATION', None):
    from channels.management.commands.runserver import Command as BaseCommand
else:
    from django.core.management.commands.runserver import Command as BaseCommand




class Command(BaseCommand):
    def _register_addon(self):
        def register_addon():
            time.sleep(0.1)
            jira_addon = JiraAddon()
            confluence_addon = ConfluenceAddon()
            jira_addon.register(port=self.port)
            confluence_addon.register(port=self.port)

        th = threading.Thread(target=register_addon, name='RegisterAddon')
        th.start()

    def get_handler(self, *args, **options):
        # WSGI
        handler = super(Command, self).get_handler(*args, **options)
        self._register_addon()
        return handler


    def get_application(self, *args, **kwargs):
        # ASGI
        application = super().get_application(*args, **kwargs)
        self._register_addon()
        return application
