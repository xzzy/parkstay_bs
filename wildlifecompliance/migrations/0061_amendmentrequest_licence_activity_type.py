# -*- coding: utf-8 -*-
# Generated by Django 1.10.8 on 2018-07-09 23:56
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wildlifecompliance', '0060_auto_20180709_0858'),
    ]

    operations = [
        migrations.AddField(
            model_name='amendmentrequest',
            name='licence_activity_type',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='wildlifecompliance.WildlifeLicenceActivityType'),
        ),
    ]