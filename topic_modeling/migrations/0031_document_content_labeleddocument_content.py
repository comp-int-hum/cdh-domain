# Generated by Django 4.0.4 on 2022-05-23 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0030_remove_document_content_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='content',
            field=models.BinaryField(null=True),
        ),
        migrations.AddField(
            model_name='labeleddocument',
            name='content',
            field=models.BinaryField(null=True),
        ),
    ]
