from django.test import TestCase, Client, tag
from django.contrib.auth import get_user_model
from djangoplicity.visits.models import Activity, ActivityProxy, Language, Reservation, Showing
from djangoplicity.media.models import Image
from faker import Faker
from datetime import datetime, timedelta
import pytz

UserModel = get_user_model()


def create_activity():
    image = Image.objects.get(pk="image-1")
    return Activity.objects.create(
            id="test-activity",
            lang="en",
            source=None,
            translation_ready=False,
            name="Public Visit Test Activity",
            observatory="Test Activity",
            meeting_point="Security Gate",
            travel_info_url="https://site.com/public/travel/",
            map_url="https://site.com/public/travel/map/",
            duration="00:06:00",
            latest_reservation_time=24,
            min_participants=6,
            max_participants=10,
            slogan="",
            description="",
            published=False,
            safety_form_text=None,
            disclaimer_form_text=None,
            conduct_form_text=None,
            key_visual_en=image,
            key_visual_es=None,
            offered_languages=[
                "en",
                "es"
            ]
        )


class ActivityTestCase(TestCase):
    fixtures = ['visits']
    fake = Faker()

    def setUp(self):
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@newsletters.org',
            password='password123'
        )
        self.client.force_login(self.admin_user)

    def test_create_activity(self):
        activity = create_activity()
        self.assertEqual(activity.lang, 'en')
        self.assertEqual(activity.name, 'Public Visit Test Activity')
        self.assertEqual("/visits/test-activity/", activity.get_absolute_url())

    def test_create_language(self):
        language = Language.objects.create(
            code="de",
            name="deutsch"
        )
        self.assertEqual(language.code, "de")
        self.assertEqual(language.name, "deutsch")


class ShowingTestCase(TestCase):
    fixtures = ['visits']
    fake = Faker()

    def test_create_showing(self):
        activity = create_activity()
        start_time = datetime.now(pytz.utc)
        end_time = start_time + timedelta(hours=6)
        showing = Showing(
            activity=activity,
            start_time=start_time,
            end_time=end_time,
            private=False,
            max_spaces_per_reservation=4,
            total_spaces=20,
            free_spaces=20
        )
        showing.save()
        print(showing.get_absolute_url())
        self.assertIsInstance(showing, Showing)
        self.assertEqual(showing.get_absolute_url(), "/visits/booking/%s/" % showing.pk)

