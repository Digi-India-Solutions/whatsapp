# Generated by Django 5.1 on 2024-09-09 07:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('testing_collection', '0011_customuser_email_customuser_first_name_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='MessageTemplate',
        ),
        migrations.DeleteModel(
            name='WhatsAppTemplate',
        ),
    ]
