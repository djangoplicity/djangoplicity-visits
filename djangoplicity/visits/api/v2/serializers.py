import pytz
from django.utils import timezone
from rest_framework import serializers
from djangoplicity.visits.models import Showing


class ShowingSerializer(serializers.ModelSerializer):
    start_time = serializers.SerializerMethodField()
    free_spaces = serializers.IntegerField()
    formatted_start_time = serializers.SerializerMethodField()

    def get_start_time(self, obj):
        return obj.start_date_tz

    def get_formatted_start_time(self, obj): # noqa
        formatted_time = obj.start_date_tz.strftime('%A %d %b %Y, %I:%M %p')
        return f"{formatted_time} {obj.activity.timezone_abbreviation}"

    class Meta:
        model = Showing
        fields = ['id', 'start_time', 'formatted_start_time', 'free_spaces']
