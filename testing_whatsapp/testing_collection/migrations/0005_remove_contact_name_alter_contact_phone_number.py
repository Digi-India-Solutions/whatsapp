# Generated by Django 5.1 on 2024-09-03 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testing_collection', '0004_remove_whatsapptemplate_button_action_url_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='contact',
            name='name',
        ),
        migrations.AlterField(
            model_name='contact',
            name='phone_number',
            field=models.CharField(max_length=12, unique=True),
        ),
    ]
