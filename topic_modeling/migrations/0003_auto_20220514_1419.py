# Generated by Django 3.1.14 on 2022-05-14 18:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0002_lexicon_lexicon'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='message',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='state',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='task_id',
        ),
    ]
