# Generated by Django 4.0.6 on 2022-07-29 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('machine_learning', '0002_machinelearningmodel_version_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='machinelearningmodel',
            name='url',
            field=models.CharField(max_length=2000, null=True),
        ),
    ]