# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-06-10 19:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0004_auto_20210610_1824'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='accept_conduct_form',
            field=models.BooleanField(default=False, verbose_name='Accept Conduct Form'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='accept_disclaimer_form',
            field=models.BooleanField(default=False, verbose_name='Accept Disclaimer Form'),
        ),
        migrations.AddField(
            model_name='reservation',
            name='accept_safety_form',
            field=models.BooleanField(default=False, verbose_name='Accept Safety Form'),
        ),
    ]
