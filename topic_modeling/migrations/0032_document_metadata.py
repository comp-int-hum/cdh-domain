# Generated by Django 4.0.4 on 2022-05-23 15:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0031_document_content_labeleddocument_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='metadata',
            field=models.JSONField(default=dict),
        ),
    ]