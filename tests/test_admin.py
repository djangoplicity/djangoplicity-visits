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

    def formset_data(self, values, check_in=()):
        data = {
            'form-TOTAL_FORMS': str(len(values)),
            'form-INITIAL_FORMS': str(len(values)),
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
        }
        for i, (reservation, checked) in enumerate(values):
            data['form-{}-id'.format(i)] = reservation.pk
            # An unchecked checkbox is not sent in the POST
            if checked:
                data['form-{}-attendance_confirmed'.format(i)] = 'on'
            if reservation in check_in:
                data['form-{}-check_in'.format(i)] = 'on'
        return data

    # test call list only shows confirmed reservations sorted by vehicle plate
    def test_call_list_view(self):
        response = self.client.get(self.url)

        plates = [form.instance.vehicle_plate for form in response.context['formset'].forms]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.waiting.is_waiting_list)
        self.assertEqual(['AAAA-11', 'BBBB-22'], plates)
        self.assertEqual(0, response.context['summary']['confirmed'])
        self.assertEqual(2, response.context['summary']['pending'])
        self.assertEqual(0, response.context['summary']['check_in'])

    # test attendance can be updated without changing the waiting list
    def test_update_attendance_confirmed(self):
        response = self.client.post(self.url, self.formset_data([
            (self.reservation_a, True),
            (self.reservation_b, False),
        ]))

        self.reservation_a.refresh_from_db()
        self.reservation_b.refresh_from_db()
        self.waiting.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.reservation_a.attendance_confirmed)
        self.assertFalse(self.reservation_b.attendance_confirmed)
        self.assertFalse(self.waiting.attendance_confirmed)
        self.assertFalse(self.reservation_a.is_waiting_list)
        self.assertTrue(self.waiting.is_waiting_list)

        # Back to pending (uncheck)
        self.client.post(self.url, self.formset_data([
            (self.reservation_a, False),
            (self.reservation_b, False),
        ]))
        self.reservation_a.refresh_from_db()
        self.assertFalse(self.reservation_a.attendance_confirmed)

    # test check in can be updated from the call list
    def test_update_check_in(self):
        response = self.client.post(self.url, self.formset_data([
            (self.reservation_a, False),
            (self.reservation_b, False),
        ], check_in=[self.reservation_a]))

        self.reservation_a.refresh_from_db()
        self.reservation_b.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.reservation_a.check_in)
        self.assertFalse(self.reservation_b.check_in)
        self.assertFalse(self.reservation_a.attendance_confirmed)
        summary = self.client.get(self.url).context['summary']
        self.assertEqual(2, summary['check_in'])
        self.assertEqual(1, summary['check_in_reservations'])

        # Back to not checked in (uncheck)
        self.client.post(self.url, self.formset_data([
            (self.reservation_a, False),
            (self.reservation_b, False),
        ]))
        self.reservation_a.refresh_from_db()
        self.assertFalse(self.reservation_a.check_in)

    # test check in count only counts spaces of confirmed reservations
    def test_check_in_count(self):
        self.assertEqual(0, self.showing.check_in_count())

        for reservation in (self.reservation_a, self.waiting):
            reservation.check_in = True
            reservation.save(skip_waiting_list_calc=True)

        self.assertEqual(2, self.showing.check_in_count())

        response = self.client.get('/admin/visits/showing/')
        showing = response.context['cl'].result_list.get(pk=self.showing.pk)
        self.assertEqual(2, response.context['cl'].model_admin.check_in_count(showing))

    # test showings created before the check in existed show N/A
    def test_check_in_count_not_apply(self):
        self.showing.reservation_set.update(check_in=None)

        self.assertIsNone(self.showing.check_in_count())
        self.assertEqual('N/A', self.client.get(self.url).context['summary']['check_in'])

        response = self.client.get('/admin/visits/showing/')
        showing = response.context['cl'].result_list.get(pk=self.showing.pk)
        self.assertEqual('N/A', response.context['cl'].model_admin.check_in_count(showing))

        # Saving the call list without checking anything keeps the reservations as N/A
        self.client.post(self.url, self.formset_data([
            (self.reservation_a, False),
            (self.reservation_b, False),
        ]))
        self.assertIsNone(self.showing.check_in_count())

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
