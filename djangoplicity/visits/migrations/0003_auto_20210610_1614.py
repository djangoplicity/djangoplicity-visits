# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2021-06-10 16:14
from __future__ import unicode_literals

from django.db import migrations
import djangoplicity.metadata.archives.fields


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0002_auto_20210602_1655'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='description',
            field=djangoplicity.metadata.archives.fields.AVMDescriptionField(blank=True, help_text='Full caption and related description text for the image resource.', null=True),
        ),
    ]
