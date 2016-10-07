# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-06-19 16:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0018_auto_20160619_1600'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='photo',
            name='media_id',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='media_mime_type',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='thumbnail_id',
        ),
        migrations.RemoveField(
            model_name='photo',
            name='thumbnail_mime_type',
        ),
        migrations.AddField(
            model_name='photo',
            name='file',
            field=models.ImageField(default='', upload_to='', verbose_name='File'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='photo',
            name='thumbnail',
            field=models.ImageField(blank=True, null=True, upload_to='', verbose_name='Thumbnail'),
        ),
    ]