# Generated by Django 3.1.2 on 2021-10-07 15:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('atlassian_connect_django', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='securitycontext',
            name='oauth_client_id',
            field=models.CharField(max_length=512, null=True),
        ),
    ]
