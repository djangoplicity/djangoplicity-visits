# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2022-11-30 08:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0009_auto_20221003_1931'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='vehicle_plate',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
