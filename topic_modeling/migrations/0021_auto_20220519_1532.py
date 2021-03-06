# Generated by Django 3.1.14 on 2022-05-19 19:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0020_auto_20220515_1940'),
    ]

    operations = [
        migrations.AlterField(
            model_name='output',
            name='collection',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='topic_modeling.collection'),
        ),
        migrations.AlterField(
            model_name='output',
            name='lexicon',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='topic_modeling.lexicon'),
        ),
        migrations.AlterField(
            model_name='output',
            name='model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='topic_modeling.topicmodel'),
        ),
    ]
