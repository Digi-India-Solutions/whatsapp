# Generated by Django 5.1 on 2024-09-09 08:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testing_collection', '0013_dashboardmessagestatus'),
    ]

    operations = [
        migrations.AddField(
            model_name='dashboardmessagestatus',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='message_status', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='dashboardmessagestatus',
            name='delivered_message',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='dashboardmessagestatus',
            name='read_message',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='dashboardmessagestatus',
            name='sent_message',
            field=models.IntegerField(default=0),
        ),
    ]
