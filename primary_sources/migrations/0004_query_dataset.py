# Generated by Django 4.0.4 on 2022-06-25 21:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('primary_sources', '0003_query'),
    ]

    operations = [
        migrations.AddField(
            model_name='query',
            name='dataset',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='primary_sources.dataset'),
        ),
    ]