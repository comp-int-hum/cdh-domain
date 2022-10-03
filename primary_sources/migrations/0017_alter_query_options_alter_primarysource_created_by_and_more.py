# Generated by Django 4.0.7 on 2022-09-13 15:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('primary_sources', '0016_alter_query_sparql'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='query',
            options={'verbose_name_plural': 'Queries'},
        ),
        migrations.AlterField(
            model_name='primarysource',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='primarysource',
            name='message',
            field=models.TextField(editable=False, null=True),
        ),
        migrations.AlterField(
            model_name='primarysource',
            name='metadata',
            field=models.JSONField(default=dict, editable=False),
        ),
        migrations.AlterField(
            model_name='primarysource',
            name='state',
            field=models.CharField(choices=[('PR', 'processing'), ('ER', 'error'), ('CO', 'complete')], default='PR', editable=False, max_length=2),
        ),
        migrations.AlterField(
            model_name='primarysource',
            name='task_id',
            field=models.CharField(editable=False, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='query',
            name='created_by',
            field=models.ForeignKey(editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='query',
            name='metadata',
            field=models.JSONField(default=dict, editable=False),
        ),
    ]