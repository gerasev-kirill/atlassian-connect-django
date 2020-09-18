# -*- coding: utf-8 -*-


from django.core.exceptions import PermissionDenied

def jwt_required(function):
    def decorator(request, *args, **kwargs):
        sc = getattr(request, 'atlassian_security_context', None)
        model = getattr(request, 'atlassian_model', None)
        if not sc or not model:
            raise PermissionDenied
        else:
            return function(request, *args, **kwargs)
    return decorator
