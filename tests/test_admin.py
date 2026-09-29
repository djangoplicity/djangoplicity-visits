from django.test import Client
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.core import mail
from .factories import factory_activity, factory_showing, factory_reservation


class TestShowingCallListAdmin(TransactionTestCase):
    fixtures = ['visits']

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin1',
            email='admin1@newsletters.org',
            password='password123'
        )
        self.client.force_login(self.admin_user)

        self.activity = factory_activity({
            'enable_waiting_list': True,
            'contact_emails_notify': 'team@visits.org',
        })
        self.showing = factory_showing(self.activity, {'total_spaces': 4})
        self.showing.save()

        # Confirmed reservations (4 spaces) and one in the waiting list
        self.reservation_b = factory_reservation(self.showing, {'vehicle_plate': 'BBBB-22', 'n_spaces': 2})
        self.reservation_b.save()
        self.reservation_a = factory_reservation(self.showing, {'vehicle_plate': 'AAAA-11', 'n_spaces': 2})
        self.reservation_a.save()
        self.waiting = factory_reservation(self.showing, {'vehicle_plate': 'CCCC-33', 'n_spaces': 1})
        self.waiting.save()

        self.url = '/admin/visits/showing/{}/call-list/'.format(self.showing.pk)

    def formset_data(self, values):
        data = {
            'form-TOTAL_FORMS': str(len(values)),
            'form-INITIAL_FORMS': str(len(values)),
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
        }
        for i, (reservation, value) in enumerate(values):
            data['form-{}-id'.format(i)] = reservation.pk
            data['form-{}-attendance_confirmed'.format(i)] = value
        return data

    # test call list only shows confirmed reservations sorted by vehicle plate
    def test_call_list_view(self):
        response = self.client.get(self.url)

        plates = [form.instance.vehicle_plate for form in response.context['formset'].forms]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.waiting.is_waiting_list)
        self.assertEqual(['AAAA-11', 'BBBB-22'], plates)
        self.assertEqual(2, response.context['summary']['not_reviewed'])

    # test attendance can be updated without changing the waiting list
    def test_update_attendance_confirmed(self):
        response = self.client.post(self.url, self.formset_data([
            (self.reservation_a, 'true'),
            (self.reservation_b, 'false'),
        ]))

        self.reservation_a.refresh_from_db()
        self.reservation_b.refresh_from_db()
        self.waiting.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(True, self.reservation_a.attendance_confirmed)
        self.assertEqual(False, self.reservation_b.attendance_confirmed)
        self.assertEqual(None, self.waiting.attendance_confirmed)
        self.assertFalse(self.reservation_a.is_waiting_list)
        self.assertTrue(self.waiting.is_waiting_list)

        # Back to not reviewed
        self.client.post(self.url, self.formset_data([
            (self.reservation_a, 'unknown'),
            (self.reservation_b, 'false'),
        ]))
        self.reservation_a.refresh_from_db()
        self.assertEqual(None, self.reservation_a.attendance_confirmed)

    # test cancel reservation from the admin
    def test_cancel_reservation(self):
        cancel_url = '{}cancel/{}/'.format(self.url, self.reservation_a.pk)

        response = self.client.get(cancel_url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(cancel_url)
        self.showing.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.url, response.url)
        self.assertFalse(self.showing.reservation_set.filter(pk=self.reservation_a.pk).exists())
        self.assertEqual(2, self.showing.free_spaces)
        # Visits team email + visitor email
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(['team@visits.org'], mail.outbox[0].to)
        self.assertEqual([self.reservation_a.email], mail.outbox[1].to)

    # test reservation must belong to the showing
    def test_cancel_reservation_other_showing(self):
        other_showing = factory_showing(self.activity, {})
        other_showing.save()

        response = self.client.post('/admin/visits/showing/{}/call-list/cancel/{}/'.format(
            other_showing.pk, self.reservation_a.pk))

        self.assertEqual(response.status_code, 404)
        self.assertTrue(self.showing.reservation_set.filter(pk=self.reservation_a.pk).exists())

    # test staff user without reservation permissions
    def test_call_list_without_permission(self):
        staff_user = get_user_model().objects.create_user(
            username='staff1',
            email='staff1@newsletters.org',
            password='password123',
            is_staff=True
        )
        client = Client()
        client.force_login(staff_user)

        self.assertEqual(client.get(self.url).status_code, 403)
        self.assertEqual(client.post('{}cancel/{}/'.format(self.url, self.reservation_a.pk)).status_code, 403)
        self.assertTrue(self.showing.reservation_set.filter(pk=self.reservation_a.pk).exists())
