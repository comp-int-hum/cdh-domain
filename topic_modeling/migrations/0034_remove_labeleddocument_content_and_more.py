# Generated by Django 4.0.4 on 2022-05-25 00:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('topic_modeling', '0033_remove_document_content_document_text'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='labeleddocument',
            name='content',
        ),
        migrations.CreateModel(
            name='LabeledDocumentSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.JSONField(null=dict)),
                ('labeled_document', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='topic_modeling.labeleddocument')),
            ],
        ),
    ]