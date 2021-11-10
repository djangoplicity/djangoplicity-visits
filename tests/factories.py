from djangoplicity.visits.models import Activity, ActivityProxy, Language, Reservation, Showing
from djangoplicity.media.models import Image
from faker.factory import Factory
from datetime import timedelta

Faker = Factory.create
fake = Faker()


# Factory to create a Activity
def factory_activity(data):

    default = {
        "id": "test-activity",
        "lang": "en",
        "source": None,
        "translation_ready": False,
        "name": fake.name(),
        "observatory": fake.company(),
        "meeting_point": fake.street_name(),
        "travel_info_url": fake.url(),
        "map_url": fake.url(),
        "duration": "00:06:00",
        "latest_reservation_time": 24,
        "min_participants": fake.random_element([5, 10]),
        "max_participants": fake.random_element([10, 15, 20]),
        "slogan": fake.text(),
        "description": "",
        "published": False,
        "safety_form_text": fake.text(),
        "disclaimer_form_text": fake.text(),
        "conduct_form_text": fake.text(),
        "key_visual_en": fake.random_element(Image.objects.all()),
        "key_visual_es": None,
        "offered_languages": [
            "en",
            "es"
        ]
    }
    if data is not None:
        default.update(data)
    return Activity.objects.create(**default)


# Factory to create random showing
def factory_showing(activity, data=None):

    start_time = fake.date_time()
    end_time = start_time + timedelta(hours=6)

    default = {
        "activity": activity,
        "start_time": start_time,
        "end_time": end_time,
        "private": fake.boolean(),
        "max_spaces_per_reservation": 4,
        "total_spaces": fake.random_element([10, 15, 20]),
    }
    if data is not None:
        default.update(data)

    return Showing(**default)


# Factory to create random reservation
def factory_reservation(showing, data=None):

    default = {
        "showing": showing,
        "name": fake.name(),
        "phone": fake.phone_number(),
        "alternative_phone": fake.phone_number(),
        "email": fake.email(),
        "country": fake.country(),
        "language": fake.random_element(Language.objects.all()),
        "n_spaces": fake.random.randint(1, 6)
    }
    if data is not None:
        default.update(data)

    return Reservation(**default)
