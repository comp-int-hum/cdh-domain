# Generated by Django 4.0.4 on 2022-05-21 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cdh', '10008_auto_20220510_1309'),
    ]

    operations = [
        migrations.AlterField(
            model_name='slide',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='slidepage',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
