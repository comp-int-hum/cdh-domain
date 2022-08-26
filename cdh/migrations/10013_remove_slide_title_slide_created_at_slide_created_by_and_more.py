# Generated by Django 4.0.6 on 2022-08-15 19:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import markdownfield.models


class Migration(migrations.Migration):

    dependencies = [
        ('cdh', '10012_alter_slide_title_alter_slidepage_name'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='slide',
            name='title',
        ),
        migrations.AddField(
            model_name='slide',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='slide',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='slide',
            name='metadata',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='slide',
            name='modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='slide',
            name='name',
            field=models.CharField(default='test', max_length=2000),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='slidepage',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='slidepage',
            name='created_by',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='slidepage',
            name='metadata',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='slidepage',
            name='modified_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='slidepage',
            name='name',
            field=models.CharField(max_length=2000),
        ),
        migrations.CreateModel(
            name='ResearchArtifact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('metadata', models.JSONField(default=dict)),
                ('name', models.CharField(max_length=2000)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('modified_at', models.DateTimeField(auto_now=True)),
                ('author_freetext', models.TextField()),
                ('description', markdownfield.models.MarkdownField(blank=True, rendered_field='rendered_description')),
                ('rendered_description', markdownfield.models.RenderedMarkdownField(null=True)),
                ('active', models.BooleanField(default=False)),
                ('authors', models.ManyToManyField(related_name='authored_by', to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]