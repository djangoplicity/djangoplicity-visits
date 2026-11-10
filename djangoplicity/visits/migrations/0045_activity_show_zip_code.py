from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0044_activity_require_zip_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='show_zip_code',
            field=models.BooleanField(default=False, help_text='Zip Code field shown (optional) on the reservation form. Ignored if Zip Code is required'),
        ),
    ]
