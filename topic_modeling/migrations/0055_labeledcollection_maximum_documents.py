# Generated by Django 4.0.4 on 2022-07-23 21:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0054_collection_created_by_collection_metadata_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='labeledcollection',
            name='maximum_documents',
            field=models.IntegerField(default=30000),
        ),
    ]
