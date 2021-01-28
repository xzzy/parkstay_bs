# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-01-28 04:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parkstay', '0068_booking_booking_change_in_progress'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='booking_change_in_progress',
        ),
        migrations.AddField(
            model_name='booking',
            name='old_booking',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
