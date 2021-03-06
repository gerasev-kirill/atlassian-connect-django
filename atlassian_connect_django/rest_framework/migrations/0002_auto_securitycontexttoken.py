# Generated by Django 3.1.2 on 2020-11-08 05:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('atlassian_connect_django', '0001_initial'),
        ('atlassian_connect_django_rest_framework', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='securitycontexttoken',
            name='security_context',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='security_context_token', to='atlassian_connect_django.securitycontext'),
        ),
    ]
