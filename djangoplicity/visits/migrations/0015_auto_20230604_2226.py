# Generated by Django 3.1 on 2023-06-04 22:26

from django.db import migrations, models
import djangoplicity.translation.fields


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0014_auto_20230604_2050'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activity',
            name='restrictions_and_recommendations',
            field=djangoplicity.translation.fields.TranslationManyToManyField(blank=True, null=True, to='visits.RestrictionRecommendation'),
        ),
        migrations.AlterField(
            model_name='showing',
            name='max_spaces_per_reservation',
            field=models.SmallIntegerField(default=0, help_text='Maximum number of spaces per reservation'),
        ),
    ]
