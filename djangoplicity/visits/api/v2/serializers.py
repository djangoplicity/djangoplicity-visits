import pytz
from django.utils import timezone
from rest_framework import serializers
from djangoplicity.visits.models import Showing, Activity


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


class ActivitySerializer(serializers.ModelSerializer):
    key_visual_en = serializers.SerializerMethodField()
    key_visual_es = serializers.SerializerMethodField()
    # individual docs
    safety_tech_doc = serializers.SerializerMethodField()
    safety_tech_doc_es = serializers.SerializerMethodField()
    conduct_tech_doc = serializers.SerializerMethodField()
    conduct_tech_doc_es = serializers.SerializerMethodField()
    liability_tech_doc = serializers.SerializerMethodField()
    liability_tech_doc_es = serializers.SerializerMethodField()
    # group docs
    group_safety_tech_doc = serializers.SerializerMethodField()
    group_safety_tech_doc_es = serializers.SerializerMethodField()
    group_liability_tech_doc = serializers.SerializerMethodField()
    group_liability_tech_doc_es = serializers.SerializerMethodField()


    def get_key_visual_en(self, obj): # noqa
        if obj.key_visual_en:
            return obj.key_visual_en.get_absolute_url() if obj.key_visual_en else None
        return ''

    def get_key_visual_es(self, obj): # noqa
        if obj.key_visual_es:
            return obj.key_visual_es.get_absolute_url() if obj.key_visual_es else None
        return ''


    def get_safety_tech_doc(self, obj): # noqa
        if obj.safety_tech_doc:
            return obj.safety_tech_doc.resource_pdf.absolute_url if obj.safety_tech_doc else None
        return ''

    def get_safety_tech_doc_es(self, obj): # noqa
        if obj.safety_tech_doc_es:
            return obj.safety_tech_doc_es.resource_pdf.absolute_url if obj.safety_tech_doc_es else None
        return ''

    def get_conduct_tech_doc(self, obj): # noqa
        if obj.conduct_tech_doc:
            return obj.conduct_tech_doc.resource_pdf.absolute_url if obj.conduct_tech_doc else None
        return ''

    def get_conduct_tech_doc_es(self, obj): # noqa
        if obj.conduct_tech_doc_es:
            return obj.conduct_tech_doc_es.resource_pdf.absolute_url if obj.conduct_tech_doc_es else None
        return ''

    def get_liability_tech_doc(self, obj): # noqa
        if obj.liability_tech_doc:
            return obj.liability_tech_doc.resource_pdf.absolute_url if obj.liability_tech_doc else None
        return ''

    def get_liability_tech_doc_es(self, obj): # noqa
        if obj.liability_tech_doc_es:
            return obj.liability_tech_doc_es.resource_pdf.absolute_url if obj.liability_tech_doc_es else None
        return ''

    def get_group_safety_tech_doc(self, obj): # noqa
        if obj.group_safety_tech_doc:
            return obj.group_safety_tech_doc.resource_pdf.absolute_url if obj.group_safety_tech_doc else None
        return ''

    def get_group_safety_tech_doc_es(self, obj): # noqa
        if obj.group_safety_tech_doc_es:
            return obj.group_safety_tech_doc_es.resource_pdf.absolute_url if obj.group_safety_tech_doc_es else None
        return ''

    def get_group_liability_tech_doc(self, obj): # noqa
        if obj.group_liability_tech_doc:
            return obj.group_liability_tech_doc.resource_pdf.absolute_url if obj.group_liability_tech_doc else None
        return ''

    def get_group_liability_tech_doc_es(self, obj): # noqa
        if obj.group_liability_tech_doc_es:
            return obj.group_liability_tech_doc_es.resource_pdf.absolute_url if obj.group_liability_tech_doc_es else None
        return ''

    class Meta:
        model = Activity
        fields = ['id', 'name', 'title', 'slogan', 'observatory', 'key_visual_en', 'key_visual_es',
                  'duration', 'safety_tech_doc', 'conduct_tech_doc', 'liability_tech_doc',
                  'safety_tech_doc_es', 'conduct_tech_doc_es', 'liability_tech_doc_es',
                  'group_safety_tech_doc', 'group_liability_tech_doc', 'group_safety_tech_doc_es',
                  'group_liability_tech_doc_es'
                  ]


