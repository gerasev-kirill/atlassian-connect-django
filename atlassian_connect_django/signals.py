import django.dispatch


# event-like signals from https://bitbucket.org/atlassian/atlassian-connect-express/src/master/


# All products
'''
    after /installed lifecycle, ACE tries to save the client information (baseUrl, clientKey, app key, puglinsVersion, productType, publicKey, serverVersion, sharedSecret)
    in storage. If successfuly saved, this event is emitted
'''
host_settings_saved = django.dispatch.Signal()
'''
     after /installed lifecycle, ACE tries to save the client information in storage. If there's any error or problem, this event is emitted
'''
host_settings_not_saved = django.dispatch.Signal()
'''
     after an ngrok tunnel is created, ACE will try to register or install the app in a Jira or Confluence product
'''
addon_registered = django.dispatch.Signal()
'''
    ACE automatically registers webhooks and corresponding paths in the descriptor file, once it tries to authenticate and is successful, this event is emitted
'''
webhook_auth_verification_successful = django.dispatch.Signal()



# Jira/Confluence
'''
    event emitted after ACE successfully creates an ngrok tunnel
'''
localtunnel_started = django.dispatch.Signal()
'''
    when ACE receives a SIGTERM, SIGINT, and SIGUSR2 signals, it will deregister the app and this event is emitted
'''
addon_deregistered = django.dispatch.Signal()



# django

host_settings_enabled = django.dispatch.Signal()
host_settings_disabled = django.dispatch.Signal()
host_settings_pre_delete = django.dispatch.Signal()
