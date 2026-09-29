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

from functools import update_wrapper

from django.conf.urls import url
from django.contrib import admin
from django import forms
from django.core.exceptions import PermissionDenied
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from import_export.widgets import ForeignKeyWidget
from djangoplicity.contrib import admin as dpadmin
from django.conf import settings
from djangoplicity.visits.models import Activity, ActivityProxy, \
    Language, Reservation, Showing, RestrictionRecommendation, RestrictionRecommendationProxy, GroupReservation
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
                     'safety_tech_doc_es', 'conduct_tech_doc_es', 'liability_tech_doc_es', 'group_safety_tech_doc',
                     'group_liability_tech_doc', 'group_safety_tech_doc_es', 'group_liability_tech_doc_es', 
                     'photo_release_form', 'photo_release_form_es')
    richtext_fields = ('description',)
    filter_horizontal = ('offered_languages', 'restrictions_and_recommendations', 'related_activities')
    form = ActivityAdminForm

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'title', 'description', 'slogan')
        }),
        ('Details', {
            'fields': ('observatory', 'meeting_point', 'meeting_point_link', 'map_url', 'travel_info_url', 'timezone',
                       'contact_emails_notify')
        }),
        ('Individual Mandatory Agreement Documents', {
            'fields': ('key_visual_en', 'key_visual_es', 'safety_tech_doc', 'conduct_tech_doc', 'liability_tech_doc',
                       'photo_release_form', 'safety_tech_doc_es', 'conduct_tech_doc_es', 'liability_tech_doc_es', 'photo_release_form_es'),
            'classes': ('collapse',),
        }),
        ('Group Mandatory Agreement Documents', {
            'fields': ('group_safety_tech_doc', 'group_liability_tech_doc', 'group_safety_tech_doc_es',
                       'group_liability_tech_doc_es'),
            'classes': ('collapse',),
        }),
        ('Registration Settings', {
            'fields': ('latest_reservation_time', 'min_participants', 'max_participants', 'duration', 'required_vehicle_plate',
                       'require_age', 'require_rut_number', 'require_hawaii_state_id_or_drivers_license_number', 'group_enable', 'enable_waiting_list',),
            'classes': ('collapse',),
        }),
        ('Language and Accessibility', {
            'fields': ('offered_languages', 'restrictions_and_recommendations', 'related_activities'),
            'classes': ('collapse',),
        })
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['id']
        else:
            return []


class ActivityProxyAdmin(dpadmin.DjangoplicityModelAdmin):
    fields = ('lang', 'source', 'translation_ready', 'name', 'title', 'meeting_point',
              'slogan', 'description')
    list_display = ('pk', 'name')
    raw_id_fields = ('source',)
    richtext_fields = ('description',)


class ReservationResource(resources.ModelResource):
    showing = fields.Field(
        column_name='showing',
        attribute='showing',
        widget=ForeignKeyWidget(Showing, 'activity__name'))

    date = fields.Field()
    time = fields.Field()

    def dehydrate_date(self, reservation):  # noqa
        return reservation.showing.start_time.strftime('%Y-%m-%d'),

    def dehydrate_time(self, reservation):  # noqa
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
        fields = (
        'id', 'name', 'code', 'rut', 'age_range', 'phone', 'alternative_phone', 'email', 'country', 'language',
        'n_spaces', 'created', 'last_modified', 'vehicle_plate', 'accept_safety_form',
        'accept_disclaimer_form', 'accept_conduct_form', 'attendance_confirmed')
        export_order = (
        'id', 'showing', 'date', 'time', 'name', 'code', 'rut', 'age_range', 'phone', 'alternative_phone',
        'email', 'country', 'language', 'n_spaces', 'created', 'last_modified', 'vehicle_plate',
        'accept_safety_form', 'accept_disclaimer_form', 'accept_conduct_form', 'attendance_confirmed')


class ReservationAdmin(ImportExportModelAdmin):
    list_display = ('email', 'name', 'activity_name', 'showing_date', 'showing_time', 'is_waiting_list',
                    'attendance_confirmed', 'phone', 'n_spaces', 'code', 'rut', 'vehicle_plate',
                    'hawaii_state_id_or_drivers_license_number', 'zip_code', 'language', 'created', 'age_range',)
    list_filter = ('showing__activity', 'showing__start_time', 'created', 'is_waiting_list', 'attendance_confirmed')
    ordering = ['showing__start_time']
    raw_id_fields = ('showing',)
    date_hierarchy = 'showing__start_time'
    readonly_fields = ('code', 'created', 'last_modified')
    search_fields = ('email', 'name')
    list_select_related = ('showing', 'language')
    resource_class = ReservationResource

    def changelist_view(self, request, extra_context=None):
        """
        Only hide waiting list reservations in the reservation admin.
        """
        if (
            "is_waiting_list__exact" not in request.GET
            and not request.path.endswith("/change/")
        ):
            mutable_get = request.GET.copy()
            mutable_get["is_waiting_list__exact"] = "0"
            request.GET = mutable_get
        return super().changelist_view(request, extra_context)

    def save_model(self, request, obj, form, change):
        obj.save(skip_waiting_list_calc=True)

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
        if self.instance and self.instance.activity_id is not None:
            timezone_name = self.instance.activity.timezone if self.instance.activity.timezone else settings.TIME_ZONE
            self.fields['start_time'].help_text = _("Start time (timezone: {timezone_name})").format(
                timezone_name=timezone_name)
            self.fields['end_time'].help_text = _("End time (timezone: {timezone_name})").format(
                timezone_name=timezone_name)

        if self.instance.id is not None:
            timezone_name = self.instance.activity.timezone if self.instance.activity.timezone is not None \
                else settings.TIME_ZONE
            tz = timezone.pytz.timezone(timezone_name)
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
    filter_horizontal = ('offered_languages',)
    list_display = ('activity', 'get_start_time_tz', 'private', 'total_spaces',
                    'free_spaces', view_online, 'view_report')
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

    def view_report(self, obj):
        return format_html(
            '<a href="{}">View Report</a> | '
            '<a href="{}" target="_blank">Waiting List</a>',
            reverse('admin:visits_showing_call_list', args=[obj.id], current_app=self.admin_site.name),
            reverse('visits-showings-waiting-list-report', args=[obj.id])
        )

    view_report.short_description = 'View report'

    def get_urls(self):
        # Tool to wrap class method into a view
        # START: Copied from django.contrib.admin.options
        def wrap(view):
            def wrapper(*args, **kwargs):
                return self.admin_site.admin_view(view)(*args, **kwargs)
            wrapper.model_admin = self
            return update_wrapper(wrapper, view)

        info = self.model._meta.app_label, self.model._meta.model_name  # visits, showing
        # END: Copied from django.contrib.admin.options

        urlpatterns = [
            url(r'^(?P<pk>\d+)/call-list/$',
                wrap(self.call_list_view),
                name='%s_%s_call_list' % info),
            url(r'^(?P<pk>\d+)/call-list/cancel/(?P<reservation_pk>\d+)/$',
                wrap(self.cancel_reservation_view),
                name='%s_%s_cancel_reservation' % info),
        ]

        # Note, must be last one, otherwise the change view
        # consumes everything else.
        urlpatterns += super(ShowingAdmin, self).get_urls()

        return urlpatterns

    def _call_list_url(self, pk):
        return reverse('admin:visits_showing_call_list', args=[pk], current_app=self.admin_site.name)

    def _has_reservation_perm(self, request, action):
        opts = Reservation._meta
        return request.user.has_perm('%s.%s_%s' % (opts.app_label, action, opts.model_name))

    def call_list_view(self, request, pk):
        '''
        List the confirmed reservations of a showing (sorted by vehicle plate) so
        the visits team can call each visitor and mark the attendance
        '''
        request.current_app = self.admin_site.name

        if not self._has_reservation_perm(request, 'view'):
            raise PermissionDenied

        showing = get_object_or_404(Showing.objects.select_related('activity'), pk=pk)
        queryset = showing.reservation_set.filter(is_waiting_list=False) \
            .select_related('language').order_by('vehicle_plate', 'name')

        ReservationFormSet = modelformset_factory(Reservation, fields=('attendance_confirmed',), extra=0)

        if request.method == 'POST':
            if not self._has_reservation_perm(request, 'change'):
                raise PermissionDenied

            formset = ReservationFormSet(request.POST, queryset=queryset)
            if formset.is_valid():
                changed = 0
                for form in formset.forms:
                    if form.has_changed():
                        obj = form.save(commit=False)
                        # Same as ReservationAdmin.save_model, don't move reservations to/from the waiting list
                        obj.save(skip_waiting_list_calc=True)
                        self.log_change(request, obj, [{'changed': {'fields': ['attendance_confirmed']}}])
                        changed += 1

                self.message_user(request, _('%d reservation(s) updated.') % changed)
                return redirect(self._call_list_url(showing.pk))
        else:
            formset = ReservationFormSet(queryset=queryset)

        attendance = [form.instance.attendance_confirmed for form in formset.forms]

        context = dict(
            self.admin_site.each_context(request),
            title=_('Call list: %s') % showing,
            opts=self.model._meta,
            showing=showing,
            formset=formset,
            summary={
                'confirmed': attendance.count(True),
                'not_confirmed': attendance.count(False),
                'not_reviewed': attendance.count(None),
            },
            has_change_permission=self._has_reservation_perm(request, 'change'),
            has_delete_permission=self._has_reservation_perm(request, 'delete'),
        )

        return TemplateResponse(request, 'admin/visits/showing/call_list.html', context)

    def cancel_reservation_view(self, request, pk, reservation_pk):
        '''
        Cancel a reservation the same way the visitor does it (see Reservation.cancel)
        '''
        request.current_app = self.admin_site.name

        if not self._has_reservation_perm(request, 'delete'):
            raise PermissionDenied

        reservation = get_object_or_404(
            Reservation.objects.select_related('showing__activity', 'language'),
            pk=reservation_pk,
            showing__pk=pk
        )

        if request.method == 'POST':
            obj_display = str(reservation)
            self.log_deletion(request, reservation, obj_display)
            reservation.cancel()

            self.message_user(request, _('The reservation "%s" was cancelled.') % obj_display)
            return redirect(self._call_list_url(pk))

        context = dict(
            self.admin_site.each_context(request),
            title=_('Cancel reservation'),
            opts=self.model._meta,
            showing=reservation.showing,
            reservation=reservation,
        )

        return TemplateResponse(request, 'admin/visits/showing/cancel_reservation_confirm.html', context)


class GroupReservationAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'group_detail_link', 'location')
    search_fields = ('name', 'email', 'phone')
    list_filter = ('location',)

    def group_detail_link(self, obj):
        if obj.code:
            url = reverse('group-registration-update', args=[obj.code])
            return format_html('<a href="{}" target="_blank">View Group</a>', url)
        return '-'

    group_detail_link.short_description = _('view group')


def register_with_admin(admin_site):
    admin_site.register(GroupReservation, GroupReservationAdmin)
    admin_site.register(Activity, ActivityAdmin)
    admin_site.register(ActivityProxy, ActivityProxyAdmin)
    admin_site.register(Language)
    admin_site.register(Reservation, ReservationAdmin)
    admin_site.register(Showing, ShowingAdmin)
    admin_site.register(RestrictionRecommendation, RestrictionRecommendationAdmin)
    admin_site.register(RestrictionRecommendationProxy, RestrictionRecommendationProxyAdmin)


register_with_admin(admin.site)
