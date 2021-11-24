# coding=utf-8
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils.translation import gettext_lazy as _
from djangoplicity.visits.models import Language, Reservation, Showing
from .factories import factory_activity, factory_showing, factory_reservation


class ActivityTestCase(TestCase):
    fixtures = ['visits']

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@newsletters.org',
            password='password123'
        )
        self.client.force_login(self.admin_user)

    def test_create_activity(self):
        activity = factory_activity({
            'id': 'test-activity',
            'lang': 'en',
            'name': 'Public Test Activity'
        })

        self.assertEqual(activity.lang, 'en')
        self.assertEqual(str(activity), 'Public Test Activity')
        self.assertEqual("/visits/test-activity/", activity.get_absolute_url())

    def test_create_language(self):
        language = Language.objects.create(
            code="de",
            name="deutsch"
        )
        self.assertEqual(language.code, "de")
        # test unicode function
        self.assertEqual(str(language), "deutsch")
        self.assertEqual(language.name, "deutsch")


class ShowingTestCase(TransactionTestCase):
    """
    Django’s TransactionTestCase
    class wraps each test in a transaction and rolls back that transaction after each test,
    in order to provide test isolation. This means that no transaction is ever actually committed,
    thus your on_commit() callbacks will never be run.If you need to test the results of an on_commit() callback,
    use a TransactionTestCase instead.
    """
    fixtures = ['visits']
    activity = None

    def setUp(self):
        self.activity = factory_activity({})

    def test_create_showing(self):
        showing = factory_showing(self.activity, {})
        showing.save()
        self.assertIsInstance(showing, Showing)
        self.assertEqual(showing.get_absolute_url(), "/visits/booking/%s/" % showing.pk)
        self.assertEqual(showing.get_report_url(), '/visits/reports/%s/' % showing.pk)
        self.assertEqual(showing.get_activity(), self.activity)

    def test_empty_values(self):
        showing = factory_showing(self.activity, {
            'total_spaces': None,
            'free_spaces': None,
            'end_time': None
        })
        showing.save()
        self.assertEqual(showing.total_spaces, self.activity.max_participants)
        self.assertEqual(showing.end_time, showing.start_time + self.activity.duration)

    def test_update_spaces_count(self):
        activity = factory_activity({})
        showing = factory_showing(activity, {
            'total_spaces': 20,
            'free_spaces': 20
        })
        showing.save()  # transaction.on_commit
        # Reservation 1, 2, 3, 4, 5 spaces total 15 reservations
        for i in range(1, 6):
            reservation = factory_reservation(showing, {
                'n_spaces': i
            })
            reservation.save()
        showing.refresh_from_db()
        self.assertEqual(showing.free_spaces, 5)


class ReservationTestCase(TestCase):
    fixtures = ['visits']
    activity = None
    showing = None

    def setUp(self):
        self.activity = factory_activity({})
        self.showing = factory_showing(self.activity, {})
        self.showing.save()

    def test_create_reservation(self):
        reservation = factory_reservation(self.showing, {
            'code': 'abc12',
            'email': 'test@email.com',
            'n_spaces': 11
        })
        reservation.save()

        # the human - readable representation of reservation
        self.assertEqual(reservation.get_absolute_url(), '/visits/update/abc12/')
        self.assertIn('test@email.com', unicode(reservation))
        self.assertIn('11 spaces', unicode(reservation))
        self.assertIsInstance(reservation, Reservation)

    def test_send_confirmation_email(self):
        reservation = factory_reservation(self.showing, {})
        reservation.save()
        reservation.send_confirmation_email()

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, _('Reservation confirmation'))

    def test_send_reminder_email(self):
        reservation = factory_reservation(self.showing, {})
        reservation.save()
        reservation.send_reminder_email()

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, _('Reservation reminder'))

    def test_send_deleted_email(self):
        reservation = factory_reservation(self.showing, {})
        reservation.save()
        reservation.send_deleted_email()

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, _('Reservation deleted'))

    def test_send_updated_email(self):
        reservation = factory_reservation(self.showing, {})
        reservation.save()
        reservation.send_updated_email()

        # Test that one message has been sent.
        self.assertEqual(len(mail.outbox), 1)

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, _('Reservation updated'))
