# Generated by Django 4.0.7 on 2022-10-03 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0068_remove_document_collection_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topicmodel',
            name='max_context_size',
            field=models.IntegerField(default=1000, help_text='If a document has more tokens than this, it will be split up into sub-documents'),
        ),
    ]