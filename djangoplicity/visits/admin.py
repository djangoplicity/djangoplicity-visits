# -*- coding: utf-8 -*-
#
# eso-visits
# Copyright (c) 2007-2017, European Southern Observatory (ESO)
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#
#    * Neither the name of the European Southern Observatory nor the names
#      of its contributors may be used to endorse or promote products derived
#      from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY ESO ``AS IS'' AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL ESO BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
# IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE

from __future__ import unicode_literals

from django.contrib import admin
from django import forms
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from import_export.widgets import ForeignKeyWidget
from djangoplicity.contrib import admin as dpadmin
from django.conf import settings
from djangoplicity.visits.models import Activity, ActivityProxy, \
    Language, Reservation, Showing, RestrictionRecommendation, RestrictionRecommendationProxy
from django.utils.translation import gettext_lazy as _
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin


if hasattr(settings, 'ADD_NOT_CACHE_URL_PARAMETER') and settings.ADD_NOT_CACHE_URL_PARAMETER:
    CACHE_PARAMETER = '?nocache'
else:
    CACHE_PARAMETER = ''


def view_online(obj):
    url = "."
    if isinstance(obj, Activity):
        url = reverse('visits-showings-list', args=[obj.id])
    elif isinstance(obj, Showing):
        url = reverse('visits-reservation-create', args=[obj.id])
    return format_html('<a href="{}{}" target="_blank">View Online</a>', url, CACHE_PARAMETER)


def view_report(obj):
    return format_html('<a href="{}{}" target="_blank">View Report</a>',
                       reverse('visits-showings-reports-detail', args=[obj.id]), CACHE_PARAMETER)


class RestrictionRecommendationAdmin(dpadmin.DjangoplicityModelAdmin):
    list_display = ('id', 'name', 'icon_name', 'caption')


class RestrictionRecommendationProxyAdmin(RestrictionRecommendationAdmin):
    pass


class ActivityAdminForm(forms.ModelForm):
    class Meta:
        model = Activity
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['related_activities'].queryset = Activity.objects.exclude(pk=self.instance.pk)


class ActivityAdmin(dpadmin.DjangoplicityModelAdmin):
    list_display = ('id', 'name', 'timezone', view_online,)
    raw_id_fields = ('key_visual_en', 'key_visual_es', 'safety_tech_doc', 'conduct_tech_doc', 'liability_tech_doc',
                     'safety_tech_doc_es', 'conduct_tech_doc_es', 'liability_tech_doc_es')
    richtext_fields = ('description',)
    filter_horizontal = ('offered_languages', 'restrictions_and_recommendations', 'related_activities')
    form = ActivityAdminForm

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['id']
        else:
            return []


class ActivityProxyAdmin(dpadmin.DjangoplicityModelAdmin):
    fields = ('lang', 'source', 'translation_ready', 'name', 'title', 'meeting_point',
              'slogan', 'description')
    list_display = ('pk', 'name')
    raw_id_fields = ('source', )
    richtext_fields = ('description',)


class ReservationResource(resources.ModelResource):
    showing = fields.Field(
        column_name='showing',
        attribute='showing',
        widget=ForeignKeyWidget(Showing, 'activity__name'))

    date = fields.Field()
    time = fields.Field()

    def dehydrate_date(self, reservation): # noqa
        return reservation.showing.start_time.strftime('%Y-%m-%d'),

    def dehydrate_time(self, reservation): # noqa
        if reservation.showing.activity.timezone:
            return '{} {}'.format(
                reservation.showing.start_date_tz.strftime('%I:%M %p'),
                reservation.showing.activity.timezone_abbreviation
            )
        else:
            return '{}'.format(
                reservation.showing.start_date_tz.strftime('%I:%M %p %Z')
            )

    class Meta:
        model = Reservation
        fields = ('id', 'name', 'code', 'rut', 'age_range', 'phone', 'alternative_phone', 'email', 'country', 'language',
                  'n_spaces', 'created', 'last_modified', 'vehicle_plate', 'accept_safety_form',
                  'accept_disclaimer_form', 'accept_conduct_form')
        export_order = ('id', 'showing', 'date', 'time',  'name', 'code', 'rut', 'age_range', 'phone', 'alternative_phone',
                        'email', 'country', 'language', 'n_spaces', 'created', 'last_modified', 'vehicle_plate',
                        'accept_safety_form', 'accept_disclaimer_form', 'accept_conduct_form')


class ReservationAdmin(ImportExportModelAdmin):
    list_display = ('email', 'name', 'activity_name', 'showing_date', 'showing_time', 'phone', 'n_spaces', 'code',
                    'rut', 'vehicle_plate', 'language', 'created', 'age_range', )
    list_filter = ('showing__activity', 'showing__start_time', 'created')
    ordering = ['showing__start_time']
    raw_id_fields = ('showing', )
    date_hierarchy = 'showing__start_time'
    readonly_fields = ('code', 'created', 'last_modified')
    search_fields = ('email', 'name')
    list_select_related = ('showing', 'language')
    resource_class = ReservationResource

    def showing_date(self, obj):
        return obj.showing.start_time.strftime('%Y-%m-%d'),
    showing_date.short_description = _('Showing Date')

    def showing_time(self, obj):
        if obj.showing.activity.timezone:
            return '{} {}'.format(
                obj.showing.start_date_tz.strftime('%I:%M %p'),
                obj.showing.activity.timezone_abbreviation
            )
        else:
            return '{}'.format(obj.showing.start_date_tz.strftime('%I:%M %p %Z'))
    showing_time.short_description = _('Showing Time')

    def activity_name(self, obj):
        return obj.showing.activity.name
    activity_name.short_description = _('Activity Name')


class ShowingAdminForm(forms.ModelForm):
    class Meta:
        model = Showing
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ShowingAdminForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.activity:
            timezone_name = self.instance.activity.timezone if self.instance.activity.timezone else settings.TIME_ZONE
            self.fields['start_time'].help_text = _("Start time (timezone: {timezone_name})").format(
                timezone_name=timezone_name)
            self.fields['end_time'].help_text = _("End time (timezone: {timezone_name})").format(
                timezone_name=timezone_name)

        if self.instance.id is not None:
            tz = timezone.pytz.timezone(self.instance.activity.timezone)
            self.initial['start_time'] = self.instance.start_time.astimezone(tz)
            self.initial['end_time'] = self.instance.end_time.astimezone(tz)

    def save(self, commit=True):
        instance = super().save(commit=False)
        activity_timezone = instance.activity.pytz_timezone
        if instance.start_time is not None:
            instance.start_time = activity_timezone.localize(instance.start_time)
        if instance.end_time is not None:
            instance.end_time = activity_timezone.localize(instance.end_time)
        if commit:
            instance.save()
        return instance


class ShowingAdmin(dpadmin.DjangoplicityModelAdmin):
    form = ShowingAdminForm
    filter_horizontal = ('offered_languages', )
    list_display = ('activity', 'get_start_time_tz', 'private', 'total_spaces',
                    'free_spaces', view_online, view_report)
    list_filter = ('activity', 'private')
    readonly_fields = ('free_spaces',)

    def get_start_time_tz(self, obj):
        """
        This method returns the start time of the Showing instance, converted
        to the timezone of the associated Activity.
        """
        return f"{obj.start_date_tz.strftime('%A %d %b %Y, %I:%M %p')} {obj.activity.timezone_abbreviation}"

    get_start_time_tz.short_description = 'Start time (TZ)'
    get_start_time_tz.admin_order_field = 'start_time'


def register_with_admin(admin_site):
    admin_site.register(Activity, ActivityAdmin)
    admin_site.register(ActivityProxy, ActivityProxyAdmin)
    admin_site.register(Language)
    admin_site.register(Reservation, ReservationAdmin)
    admin_site.register(Showing, ShowingAdmin)
    admin_site.register(RestrictionRecommendation, RestrictionRecommendationAdmin)
    admin_site.register(RestrictionRecommendationProxy, RestrictionRecommendationProxyAdmin)


register_with_admin(admin.site)
