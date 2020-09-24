import binascii
import os

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from atlassian_connect_django.models.connect import SecurityContext



class SecurityContextToken(models.Model):
    """
    The default authorization token model.
    """
    key = models.CharField(_("Key"), max_length=40, primary_key=True)
    security_context = models.OneToOneField(
        SecurityContext, related_name='security_context_token',
        on_delete=models.CASCADE
    )
    atlassian_user_account_id = models.CharField(_("Atlassian user id"), max_length=50)
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    class Meta:
        abstract = 'atlassian_connect_django.rest_framework' not in settings.INSTALLED_APPS
        verbose_name = _("Token for atlassian security context")
        verbose_name_plural = _("Tokens for atlassian security context")

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super(SecurityContextToken, self).save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key
