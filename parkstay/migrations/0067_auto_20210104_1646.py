# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-01-04 08:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('parkstay', '0066_emailgroup'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='campsitebooking',
            unique_together=set([]),
        ),
    ]
