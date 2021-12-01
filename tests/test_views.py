from django.test import Client
from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from .factories import factory_activity, factory_showing, factory_reservation, create_datetime
from django.core import mail
from django.forms.models import model_to_dict

user_client = Client()
public_client = Client()


class TestShowingView(TransactionTestCase):
    fixtures = ['visits']
    activity = None

    def setUp(self):
        self.user_client = user_client
        self.public_client = public_client
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin1',
            email='admin1@newsletters.org',
            password='password123'
        )
        self.user_client.force_login(self.admin_user)
        self.activity = factory_activity({})

    # test showing report view
    def test_showing_report_list_view(self):
        user_response = self.user_client.get('/visits/reports/')
        public_response = self.public_client.get('/visits/reports/')

        self.assertEquals(user_response.status_code, 200)
        self.assertEquals(public_response.status_code, 302)

    # test showing detail view
    def test_showing_detail_view(self):
        # Create a public showing at 2021-12-01 23:59
        showing = factory_showing(self.activity, {
            "private": False,
            "start_time": create_datetime(2021, 12, 1, 23, 59, 59, 00000)
        })
        showing.save()
        # Create 3 reservations
        for i in range(1, 4):
            r = factory_reservation(showing, {
                "email": "reservation{}@mail.com".format(str(i))
            })
            r.save()
        # request reservation report
        response = self.user_client.get('/visits/reports/{}/'.format(showing.id))

        self.assertIn("Public Visits Reports", response.content)
        self.assertIn("2021-12-01 23:59", response.content)
        self.assertIn("reservation1@mail.com", response.content)
        self.assertIn("reservation2@mail.com", response.content)
        self.assertIn("reservation3@mail.com", response.content)
        self.assertEquals(response.status_code, 200)

    # Activity showing list
    def test_showing_list_by_activity(self):
        factory_activity({
            'id': 'test-activity-name',
            'name': 'Test Activity Name'

        })
        response = self.user_client.get('/visits/test-activity-name/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('Test Activity Name', response.content)

    # Activity not exist
    def test_activity_not_found(self):
        response = self.user_client.get('/visits/does-not-exist/')
        self.assertEqual(response.status_code, 302)


class TestReservationView(TransactionTestCase):
    fixtures = ['visits']
    activity = None
    showing = None
    create_url = None
    data = {}

    def setUp(self):
        self.user_client = user_client
        self.public_client = public_client
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin1',
            email='admin1@newsletters.org',
            password='password123'
        )
        self.user_client.force_login(self.admin_user)
        self.activity = factory_activity({})
        self.showing = factory_showing(self.activity, {
            "private": False,
            "total_spaces": 20
        })
        self.showing.save()
        # set URL to showing post view
        self.create_url = "/visits/booking/{}/".format(self.showing.id)

        self.data = {
            "showing": self.showing.id,
            "name": "Jhon Doe",
            "phone": "091 123 4356",
            "email": "jdoe@mail.com",
            "email_confirm": "jdoe@mail.com",
            "country": "japan",
            "language": "en",
            "n_spaces": 4,  # max spaces per person allowed
            "submit": "Submit",
            "accept_safety_form": "on",
            "accept_disclaimer_form": "on",
            "accept_conduct_form": "on",
        }

    def test_create_reservation(self):
        # count before to reservation
        count_before = self.showing.reservation_set.count()
        response = self.client.post(self.create_url, data=self.data, follow=True)

        # Count after to create a new reservation
        self.showing.refresh_from_db()
        count_after = self.showing.reservation_set.count()

        self.assertEqual(count_after, count_before + 1)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(response.status_code, 200)

    def test_bad_email_confirmation_to_create_reservation(self):
        data = self.data.copy()
        data.update({
            "email": "jdoebad@mail.com",
            "email_confirm": "jdoe@mail.com",
            "n_spaces": 1,
        })

        # count before to reservation
        count_before = self.showing.reservation_set.count()
        response = self.client.post(self.create_url, data=data)

        # Count after to create a new reservation
        self.showing.refresh_from_db()
        count_after = self.showing.reservation_set.count()

        self.assertEqual(count_after, count_before)
        self.assertEqual(response.status_code, 200)

    # update a reservation
    def test_update_reservation(self):
        reservation = factory_reservation(self.showing, {
            "code": "abc12",
            "name": "Jhon Doe",
            'n_spaces': 1,
        })
        reservation.save()

        # get reservation data
        data = model_to_dict(reservation)

        # change reservation data
        data.update({
            "name": "Larry Doe",
            'n_spaces': 2,
            "email_confirm": reservation.email,
            "accept_safety_form": "on",
            "accept_disclaimer_form": "on",
            "accept_conduct_form": "on",
            "submit": "Submit",
        })
        # Remove immutable reservation data
        data.pop('created')
        data.pop('last_modified')

        # request changes
        response = self.client.post("/visits/update/abc12/", data)

        reservation.refresh_from_db()

        self.assertEqual("Larry Doe", reservation.name)
        self.assertEqual(2, reservation.n_spaces)
        self.assertEqual('/visits/confirmed/abc12/', response.url)
        self.assertEqual(response.status_code, 302)

    # Not update reservation by email confirmation
    def test_not_allow_changes_in_reservation_lack_email_confirmation(self):
        reservation = factory_reservation(self.showing, {
            "code": "abc12",
            "name": "Jhon Doe",
            'n_spaces': 1,
        })
        reservation.save()

        # get reservation data
        data = model_to_dict(reservation)

        # change reservation data
        data.update({
            "name": "Larry Doe",
            'n_spaces': 2,
            "accept_safety_form": "on",
            "accept_disclaimer_form": "on",
            "accept_conduct_form": "on",
            "submit": "Submit",
        })
        # Remove immutable reservation data
        data.pop('created')
        data.pop('last_modified')

        # request changes
        response = self.client.post("/visits/update/abc12/", data)

        reservation.refresh_from_db()

        self.assertNotEqual("Larry Doe", reservation.name)
        self.assertNotEqual(2, reservation.n_spaces)
        self.assertEqual(response.status_code, 200)

    # test cancel reservation
    def test_cancel_reservation(self):
        reservation = factory_reservation(self.showing, {
            "code": "def12",
            "name": "Jhon Doe",
            'n_spaces': 1,
        })
        reservation.save()
        reservation_exist = True

        # Request delete
        response = self.client.post("/visits/delete/def12/")

        # Validate if still exist
        try:
            reservation.refresh_from_db()
        except reservation._meta.model.DoesNotExist:
            reservation_exist = False

        self.assertEqual(False, reservation_exist)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual("/visits/reservation-cancelled/", response.url)
        self.assertEqual(response.status_code, 302)
