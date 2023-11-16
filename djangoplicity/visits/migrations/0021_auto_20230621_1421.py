# Generated by Django 3.1 on 2023-06-21 14:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0020_auto_20230614_0735'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='showing',
            options={'ordering': ('-start_time',)},
        ),
        migrations.AddField(
            model_name='activity',
            name='related_activities',
            field=models.ManyToManyField(blank=True, related_name='_activity_related_activities_+', to='visits.Activity'),
        ),
    ]