# Generated by Django 4.0.4 on 2022-05-25 01:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0034_remove_labeleddocument_content_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='title',
            field=models.CharField(max_length=10000),
        ),
        migrations.AlterField(
            model_name='topicmodel',
            name='maximum_documents',
            field=models.IntegerField(default=500),
        ),
        migrations.AlterField(
            model_name='topicmodel',
            name='maximum_vocabulary',
            field=models.IntegerField(default=5000),
        ),
        migrations.AlterField(
            model_name='topicmodel',
            name='topic_count',
            field=models.IntegerField(default=10),
        ),
    ]
