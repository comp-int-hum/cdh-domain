# Generated by Django 4.0.4 on 2022-05-21 18:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0023_document_labeledcollection_labeleddocument_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='disk_serialized',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='disk_serialized_processed',
        ),
    ]
