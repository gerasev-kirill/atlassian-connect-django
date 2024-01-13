# Generated by Django 3.1.2 on 2020-10-24 13:02

import atlassian_connect_django.models.cache
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AtlassianUserOAuth2BearerToken',
            fields=[
                ('account_id', models.CharField(max_length=512, primary_key=True, serialize=False)),
                ('token_cache', atlassian_connect_django.models.cache.JSONField(default=dict)),
            ],
        ),
        migrations.CreateModel(
            name='SecurityContext',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shared_secret', models.CharField(max_length=512)),
                ('key', models.CharField(max_length=512)),
                ('client_key', models.CharField(max_length=512)),
                ('host', models.CharField(max_length=512)),
                ('oauth_client_id', models.CharField(max_length=512)),
                ('is_plugin_enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
