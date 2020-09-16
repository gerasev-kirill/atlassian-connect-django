# -*- coding: utf-8 -*-


from django.contrib import admin
from django_atlassian.models.connect import SecurityContext

class SecurityContextAdmin(admin.ModelAdmin):
    list_display = ['key']

admin.site.register(SecurityContext, SecurityContextAdmin)
