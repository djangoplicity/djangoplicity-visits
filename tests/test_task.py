from djangoplicity.visits.tasks import reservation_reminder
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from .factories import factory_activity, factory_showing, factory_reservation
from datetime import datetime, timedelta
from django.core import mail
import pytz
from django.utils.translation import gettext_lazy as _

utc = pytz.timezone('UCT')


class TestDjangoplicityTask(TransactionTestCase):
    fixtures = ['visits']
    activity = None
    showing = None

    def setUp(self):
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin1',
            email='admin1@newsletters.org',
            password='password123'
        )
        self.activity = factory_activity({})
        self.showing = factory_showing(self.activity, {
            "private": False,
            "total_spaces": 20,
            "start_time": datetime.now(utc) + timedelta(days=1)
        })
        self.showing.save()
        reservation = factory_reservation(self.showing, {
            "code": "abc12",
            "name": "Jhon Doe",
            'n_spaces': 1,
        })
        reservation.save()
        reservation = factory_reservation(self.showing, {
            "code": "abc13",
            "name": "Jhon Doe",
            'n_spaces': 1,
        })
        reservation.save()
        reservation.last_modified = datetime.now(utc) + timedelta(days=-1)
        reservation.save()

    def test_reservation_reminder_task(self):
        """Ensure the task runs in Celery and calls the correct function."""
        with self.settings(SITE_ENVIRONMENT='prod'):
            reservation_reminder()
            self.assertEqual(len(mail.outbox), 2)
            self.assertEqual(mail.outbox[0].subject, _('Reservation reminder'))
            self.assertEqual(mail.outbox[1].subject, _('Reservation reminder'))

    def test_reminder_not_run_develop(self):
        """Ensure the task not runs in develop."""
        with self.settings(SITE_ENVIRONMENT='dev'):
            reservation_reminder()
            self.assertEqual(len(mail.outbox), 0)
