# Generated by Django 4.0 on 2021-12-28 17:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0003_topicmodel_data_topicmodel_lowercase_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='document',
            old_name='content',
            new_name='text',
        ),
    ]