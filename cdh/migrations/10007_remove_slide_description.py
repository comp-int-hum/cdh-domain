# Generated by Django 3.1.14 on 2022-05-10 17:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdh', '10006_remove_slide_link'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='slide',
            name='description',
        ),
    ]