# Generated by Django 3.1.14 on 2022-05-15 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0011_auto_20220515_1314'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='db_serialized',
            field=models.BinaryField(null=True),
        ),
        migrations.AddField(
            model_name='topicmodel',
            name='db_serialized',
            field=models.BinaryField(null=True),
        ),
    ]