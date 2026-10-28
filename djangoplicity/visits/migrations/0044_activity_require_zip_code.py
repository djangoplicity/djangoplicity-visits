from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0043_reservation_check_in'),
    ]

    operations = [
        migrations.AddField(
            model_name='activity',
            name='require_zip_code',
            field=models.BooleanField(default=False, help_text='Zip Code required on the reservation form'),
        ),
    ]
