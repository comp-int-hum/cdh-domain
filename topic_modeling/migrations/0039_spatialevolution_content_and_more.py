# Generated by Django 4.0.4 on 2022-05-25 18:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0038_rename_has_geography_collection_has_spatiality'),
    ]

    operations = [
        migrations.AddField(
            model_name='spatialevolution',
            name='content',
            field=models.JSONField(null=dict),
            preserve_default=dict,
        ),
        migrations.AddField(
            model_name='spatialevolution',
            name='labeled_collection',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='topic_modeling.labeledcollection'),
        ),
        migrations.AddField(
            model_name='temporalevolution',
            name='content',
            field=models.JSONField(null=dict),
            preserve_default=dict,
        ),
        migrations.AddField(
            model_name='temporalevolution',
            name='labeled_collection',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='topic_modeling.labeledcollection'),
        ),
    ]