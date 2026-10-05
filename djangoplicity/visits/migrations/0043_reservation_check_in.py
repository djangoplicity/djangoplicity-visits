from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('visits', '0042_reservation_attendance_confirmed'),
    ]

    operations = [
        # Added without default so existing reservations stay NULL (N/A)
        migrations.AddField(
            model_name='reservation',
            name='check_in',
            field=models.BooleanField(null=True, help_text='Checked when the visitor arrives at the showing', verbose_name='Check in'),
        ),
        # New reservations start as not checked in
        migrations.AlterField(
            model_name='reservation',
            name='check_in',
            field=models.BooleanField(default=False, null=True, help_text='Checked when the visitor arrives at the showing', verbose_name='Check in'),
        ),
    ]
