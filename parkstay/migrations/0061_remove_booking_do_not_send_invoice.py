# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2020-09-10 03:57
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parkstay', '0060_auto_20200910_1154'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='booking',
            name='do_not_send_invoice',
        ),
    ]
