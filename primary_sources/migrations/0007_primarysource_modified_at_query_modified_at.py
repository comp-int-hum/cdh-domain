# Generated by Django 4.0.6 on 2022-07-26 21:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('primary_sources', '0006_primarysource_created_by_primarysource_metadata_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='primarysource',
            name='modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='query',
            name='modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
