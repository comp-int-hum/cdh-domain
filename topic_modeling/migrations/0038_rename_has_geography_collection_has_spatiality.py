# Generated by Django 4.0.4 on 2022-05-25 18:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0037_document_datetime_document_latitude_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='collection',
            old_name='has_geography',
            new_name='has_spatiality',
        ),
    ]
