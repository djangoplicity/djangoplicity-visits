# Generated by Django 3.1 on 2023-06-13 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0017_auto_20230613_1359'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='showing',
            name='vehicle_plate_required',
        ),
        migrations.AddField(
            model_name='activity',
            name='required_vehicle_plate',
            field=models.BooleanField(default=False, help_text='Vehicle Plate required on the reservation form'),
        ),
    ]
