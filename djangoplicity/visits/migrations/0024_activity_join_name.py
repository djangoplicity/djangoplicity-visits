# Generated by Django 3.1 on 2023-06-22 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0023_activity_showing_list_title_es'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='join_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]