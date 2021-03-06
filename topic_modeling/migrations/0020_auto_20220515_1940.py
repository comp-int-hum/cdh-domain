# Generated by Django 3.1.14 on 2022-05-15 23:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0019_output_disk_serialized'),
    ]

    operations = [
        migrations.AddField(
            model_name='topicmodel',
            name='maximum_proportion',
            field=models.FloatField(default=1.0),
        ),
        migrations.AddField(
            model_name='topicmodel',
            name='minimum_count',
            field=models.IntegerField(default=0),
        ),
    ]
