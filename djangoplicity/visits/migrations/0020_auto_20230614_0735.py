# Generated by Django 3.1 on 2023-06-14 07:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0019_auto_20230614_0734'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reservation',
            name='rut',
            field=models.IntegerField(blank=True, default=0, null=True, verbose_name='RUT Number'),
        ),
    ]