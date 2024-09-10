# Generated by Django 5.1 on 2024-08-22 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testing_collection', '0003_alter_whatsapptemplate_language_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='whatsapptemplate',
            name='button_action_url',
        ),
        migrations.RemoveField(
            model_name='whatsapptemplate',
            name='button_text',
        ),
        migrations.RemoveField(
            model_name='whatsapptemplate',
            name='content_body',
        ),
        migrations.RemoveField(
            model_name='whatsapptemplate',
            name='media_type',
        ),
        migrations.RemoveField(
            model_name='whatsapptemplate',
            name='media_url',
        ),
        migrations.RemoveField(
            model_name='whatsapptemplate',
            name='template_type',
        ),
        migrations.AddField(
            model_name='whatsapptemplate',
            name='body_text',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='whatsapptemplate',
            name='buttons',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='whatsapptemplate',
            name='category',
            field=models.CharField(choices=[('MARKETING', 'Marketing'), ('TRANSACTIONAL', 'Transactional')], default=1, max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='whatsapptemplate',
            name='footer_text',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='whatsapptemplate',
            name='header_text',
            field=models.TextField(blank=True, null=True),
        ),
    ]
