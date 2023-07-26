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

from datetime import datetime, time, timedelta
import pytz

from django.urls import reverse
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpResponseRedirect
from django.utils import timezone, translation
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView
)

from djangoplicity.visits.forms import ReservationForm
from djangoplicity.visits.models import Activity, Reservation, Showing

from djangoplicity.translation.models import translation_reverse


class ReservationCreateView(CreateView):
    model = Reservation
    form_class = ReservationForm

    def get_context_data(self, **kwargs):
        context = super(ReservationCreateView, self).get_context_data(**kwargs)
        showing = self.get_showing()
        activity = showing.get_activity()
        context['showing'] = showing
        context['activity'] = activity
        context['other_showings'] = self.get_other_showings()

        # Get the user's timezone from the request (if available)
        user_timezone = pytz.timezone(self.request.session.get('timezone', settings.TIME_ZONE))

        # Convert the user's current time to the timezone of the activity
        activity_timezone = pytz.timezone(activity.timezone if activity.timezone else settings.TIME_ZONE)
        user_now = datetime.now(user_timezone)
        activity_now = user_now.astimezone(activity_timezone)

        # Determine if it's too late to make a reservation
        context['too_late'] = (
            activity_now.date() >= activity_timezone.localize(showing.start_time).date() - timedelta(days=1)
            and activity_now.time() > time(hour=13)
        )

        return context

    def subscribe_contact(self, data): # noqa
        try:
            from djangoplicity.contacts.models import Contact, ContactGroup
            email = data.get('email')
            group_name = getattr(settings, 'VISIT_SUBSCRIBE_GROUP', 'Public NL')
            group = ContactGroup.objects.get(name=group_name)

            if not Contact.objects.filter(email=email, groups__in=[group.id]):
                contact_data = {
                    'first_name': data.get('name'),
                    'phone': data.get('phone'),
                    'email': data.get('email')
                }
                Contact.create_object(groups=[group.id], **contact_data)
        except ImportError:
            pass
        except ObjectDoesNotExist:
            pass

    def get_form_kwargs(self):
        kwargs = super(ReservationCreateView, self).get_form_kwargs()
        kwargs['showing'] = self.get_showing()

        return kwargs

    def get_initial(self):
        initial = super(ReservationCreateView, self).get_initial()
        initial['showing'] =  self.get_showing()
        return initial

    def get_other_showings(self):
        showing = self.get_showing()

        now = timezone.now()
        hours_ago = showing.activity.latest_reservation_time
        time_ago = now + timedelta(hours=hours_ago)

        return showing.activity.showings.filter(
            private=False,
            start_time__gt=time_ago,
        ).order_by('start_time')

    def get_showing(self):
        if hasattr(self, 'showing'):
            return self.showing  # pylint: disable=access-member-before-definition

        now = timezone.now()
        k = self.kwargs['showingpk']
        try:
            self.showing = Showing.objects.get(
                pk=self.kwargs['showingpk'],
                start_time__gt=now,
            )
        except Showing.DoesNotExist:
            raise Http404
        except ValueError:
            raise Http404

        return self.showing

    def get_success_url(self, **kwargs):
        self.object.send_confirmation_email()
        # return reverse('visits-reservation-confirm', args=[self.object.code])
        return translation_reverse(
            'visits-reservation-confirm',
            args=[self.object.code],
            lang=self.object.language.code)

    def form_valid(self, form):
        reservation = form.save(commit=False)
        reservation.save()
        if form.cleaned_data.get('subscribe_checkbox', False):
            self.subscribe_contact(form.cleaned_data)
        return super(ReservationCreateView, self).form_valid(form)


class ReservationDeleteView(DeleteView):
    form_class = ReservationForm
    model = Reservation
    slug_url_kwarg = 'code'
    slug_field = 'code'
    #  success_url = '/public/weekend-visits/reservation-cancelled/'

    def get_success_url(self, **kwargs):
        self.object.send_deleted_email()
        #  return reverse('visits-reservation-delete-confirm')
        return translation_reverse(
            'visits-reservation-delete-confirm',
            args=[],
            lang=self.object.language.code)


class ReservationConfirmView(DetailView):
    template_name = 'visits/reservation_confirm.html'
    model = Reservation
    slug_url_kwarg = 'code'
    slug_field = 'code'


class ReservationDeleteConfirmView(TemplateView):
    template_name = 'visits/reservation_delete_confirm.html'


class ReservationUpdateView(UpdateView):
    form_class = ReservationForm
    model = Reservation
    slug_url_kwarg = 'code'
    slug_field = 'code'
    template_name = 'visits/reservation_update.html'

    def get_context_data(self, **kwargs):
        context = super(ReservationUpdateView, self).get_context_data(**kwargs)
        reservation = self.get_object()
        showing = reservation.showing
        other_reservations = showing.reservation_set.filter(email=reservation.email).exclude(code=reservation.code)
        context['other_reservations'] = other_reservations
        context['activity'] = self.get_object().showing.get_activity()

        return context

    def get_success_url(self, **kwargs):
        self.object.send_updated_email()
        #  return reverse('visits-reservation-confirm', args=[self.object.code])
        return translation_reverse(
            'visits-reservation-confirm',
            args=[self.object.code],
            lang=self.object.language.code)


class ReservationCancelView(ReservationUpdateView):

    def get_context_data(self, **kwargs):
        context = super(ReservationCancelView, self).get_context_data(**kwargs)
        context['cancel'] = True
        return context


class ShowingListView(ListView):
    model = Showing

    def get_activity(self, pk):
        try:
            self.activity = (
                Activity.objects.fallback(
                    translation.get_language()
                ).filter(pk=pk).get()
            )
        except Activity.DoesNotExist:
            self.activity = None

        return self.activity

    def get_context_data(self, **kwargs):
        context = super(ShowingListView, self).get_context_data(**kwargs)
        context['activity'] = self.activity
        return context

    def get(self, request, *args, **kwargs):
        pk = self.kwargs.pop('pk')
        activity = self.get_activity(pk)

        if not activity:
            return HttpResponseRedirect(reverse('visits-reservation-create',
                args=[pk]))

        return super(ShowingListView, self).get(request, *args, **kwargs)

    def get_queryset(self):
        now = timezone.now()
        hours_ago = self.activity.latest_reservation_time

        time_ago = now + timedelta(hours=hours_ago)
        qs = self.activity.showings.filter(
            private=False,
            start_time__gt=time_ago
        )
        if self.activity.is_translation():
            related_activities = self.activity.source.related_activities.all()
        else:
            related_activities = self.activity.related_activities.all()

        related_showings = Showing.objects.filter(
            activity__in=related_activities,
            private=False,
            start_time__gt=time_ago
        )
        qs = qs | related_showings
        return (qs.order_by('start_time'))


class ShowingReportDetailView(DetailView):
    model = Showing
    template_name = 'visits/showing_report_detail.html'


class ShowingReportListView(ListView):
    model = Showing
    template_name = 'visits/showing_report_list.html'

    def get_queryset(self):
        return (
            super(ShowingReportListView, self).get_queryset()
            .order_by('activity__name', '-start_time')
        )
