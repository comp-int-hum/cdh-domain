# Generated by Django 4.0.7 on 2022-09-27 21:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('turkle', '0013_activeproject_activeuser_alter_batch_id_and_more'),
        ('annotation', '0002_rename_batch_annotationbatch_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='AnnotationBatch',
            new_name='Batch',
        ),
        migrations.RenameModel(
            old_name='AnnotationProject',
            new_name='Project',
        ),
    ]
