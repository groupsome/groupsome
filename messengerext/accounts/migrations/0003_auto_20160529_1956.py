# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-05-29 19:56
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20160529_1950'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='logintoken',
            name='timestamp',
        ),
        migrations.AddField(
            model_name='logintoken',
            name='created',
            field=models.DateTimeField(auto_now_add=True,
                                       default=datetime.datetime(2016, 5, 29, 19, 56, 10, 774236, tzinfo=utc),
                                       verbose_name='Created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='logintoken',
            name='latestPoll',
            field=models.DateTimeField(auto_now_add=True,
                                       default=datetime.datetime(2016, 5, 29, 19, 56, 16, 878527, tzinfo=utc),
                                       verbose_name='LatestPoll'),
            preserve_default=False,
        ),
    ]
