# Generated by Django 3.1.14 on 2022-05-14 18:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0003_auto_20220514_1419'),
    ]

    operations = [
        migrations.AlterField(
            model_name='collection',
            name='data',
            field=models.FileField(null=True, upload_to='topic_modeling/collections'),
        ),
    ]
