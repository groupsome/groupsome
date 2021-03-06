# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-08-01 02:38
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0024_group_header_version'),
        ('gallery', '0001_create_album_model_in_gallery_instead_of_home'),
    ]

    operations = [
        migrations.AddField(
            model_name='album',
            name='cover',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL,
                                    related_name='cover_of_albums', to='home.Photo'),
        ),
    ]
