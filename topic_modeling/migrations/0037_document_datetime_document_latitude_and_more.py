# Generated by Django 4.0.4 on 2022-05-25 15:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0036_spatialevolution_temporalevolution_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='datetime',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='latitude',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='longitude',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='document',
            name='year',
            field=models.IntegerField(null=True),
        ),
    ]
