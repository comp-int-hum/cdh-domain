# Generated by Django 3.1.14 on 2022-05-09 00:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cdh', '10005_auto_20220508_2036'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='slide',
            name='link',
        ),
    ]