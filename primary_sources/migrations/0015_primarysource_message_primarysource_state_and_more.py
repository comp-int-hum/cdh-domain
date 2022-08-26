# Generated by Django 4.0.6 on 2022-08-21 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('primary_sources', '0014_alter_query_primary_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='primarysource',
            name='message',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='primarysource',
            name='state',
            field=models.CharField(choices=[('PR', 'processing'), ('ER', 'error'), ('CO', 'complete')], default='PR', max_length=2),
        ),
        migrations.AddField(
            model_name='primarysource',
            name='task_id',
            field=models.CharField(max_length=200, null=True),
        ),
    ]