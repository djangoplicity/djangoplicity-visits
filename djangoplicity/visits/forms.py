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

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.db.models import Sum
from django import forms
from django.utils.translation import gettext_lazy as _
from django.conf import Settings, settings
from djangoplicity.visits.models import Reservation, GroupReservation, Activity, Showing
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV3


NOT_HAS_SYMPTOMS_LABEL = _("I declare that no one in my group has tested positive for COVID-19 or had any symptoms in "
                           "the last 10 days: "
                           "<ul class='list-unstyled'>"
                               "<li>a. Cough</li>"
                               "<li>b. Fever</li>"
                               "<li>c. Sore throat</li>"
                               "<li>d. Shortness of breath</li>"
                               "<li>e. Fatigue</li>"
                               "<li>f. Muscle or body aches</li>"
                               "<li>g. Loss of taste or smell</li>"
                               "<li>h. Nausea or vomiting</li>"
                               "<li>i. Diarrhea</li>"
                           "</ul>")

SUBSCRIBE_CHECKBOX_LABEL = _('Subscribe to news from our observatories')


class ReservationForm(forms.ModelForm):

    email_confirm = forms.EmailField(label=_('Confirm Email'))
    waiting_list_message = None

    captcha = ReCaptchaField(widget=ReCaptchaV3, required=True)

    if getattr(settings, 'VISITS_COVID_CONDITIONS', False):
        not_has_tested_positive_for_covid = forms.BooleanField(
            label=NOT_HAS_SYMPTOMS_LABEL,
            required=False,
            widget=forms.CheckboxInput(attrs={'class': 'acceptConditions covid'})
        )

    if getattr(settings, 'DISPLAY_VISITS_SUBSCRIBE_CHECKOUT', True):
        subscribe_checkbox = forms.BooleanField(
            label=SUBSCRIBE_CHECKBOX_LABEL,
            required=False,
            widget=forms.CheckboxInput()
        )

    field_order = ['name', 'phone', 'alternative_phone', 'email',
                   'email_confirm', 'country', 'language', 'vehicle_plate', 'n_spaces',
                   'rut', 'hawaii_state_id_or_drivers_license_number', 'zip_code', 
                   'age_range', 'accept_safety_form', 'accept_disclaimer_form',
                   ]

    if getattr(settings, 'VISITS_DISPLAY_ACCEPT_CONDUCT_FORM', False):
        field_order.append('accept_conduct_form')

    class Meta:
        model = Reservation
        exclude = ['code', 'created', 'last_modified', 'is_waiting_list']

    def __init__(self, *args, **kwargs):
        self.showing = kwargs.pop('showing', None)

        super(ReservationForm, self).__init__(*args, **kwargs)

        if self.showing is None:
            self.showing = self.instance.showing

        self.fields['showing'].widget = forms.HiddenInput()
        self.fields['language'].widget = forms.RadioSelect()
        languages = self.showing.offered_languages.all()
        if languages:
            self.fields['language'].choices = [(language.code, language.name) for language in languages]

        max_value = self.showing.max_spaces_per_reservation
        if max_value == 0:
            max_value = self.showing.free_spaces

        if self.showing is not None:
            self.fields['showing'].initial = self.showing.id

        # If we're editing an existing showing then max_value is max_value
        # added to the currently selected places
        if self.instance.pk:
            max_value += self.instance.n_spaces

        self.fields['n_spaces'] = forms.IntegerField(
            label=self.fields['n_spaces'].label,
            min_value=1,
            max_value=max_value,
        )
        if self.showing.max_spaces_per_reservation == 1:
            self.fields['n_spaces'].initial = 1
            self.fields['n_spaces'].widget.attrs.update({
                'readonly': True
            })

        self.fields['email'].widget.attrs.update({
            'class': 'nocopypaste'
        })
        self.fields['email_confirm'].widget.attrs.update({
            'class': 'nocopypaste'
        })

        if self.showing.activity.required_vehicle_plate:
            self.fields['vehicle_plate'].required = True
        else:
            self.fields.pop('vehicle_plate')

        if self.showing.activity.require_rut_number:
            self.fields['rut'].required = False
        else:
            self.fields.pop('rut')
        
        if self.showing.activity.require_hawaii_state_id_or_drivers_license_number:
            self.fields.pop('country')
        else:
            self.fields['country'].required = True

        if self.showing.activity.require_hawaii_state_id_or_drivers_license_number:
            self.fields.pop('language')
        else:
            self.fields['language'].required = True

        if self.showing.activity.require_hawaii_state_id_or_drivers_license_number:
            self.fields['hawaii_state_id_or_drivers_license_number'].required = True
        else:
            self.fields.pop('hawaii_state_id_or_drivers_license_number')

        if self.showing.activity.require_hawaii_state_id_or_drivers_license_number:
            self.fields['zip_code']
        else:
            self.fields.pop('zip_code')


        if self.showing.activity.require_age:
            choices = list(filter(lambda item: item[1] != Reservation.RANGE_UNKNOWN, Reservation.AGE_RANGES))
            self.fields['age_range'].choices = choices
        else:
            self.fields.pop('age_range')

        if self.showing.activity.safety_tech_doc:
            self.fields['accept_safety_form'].widget.attrs.update({
                'data-target': '#safety_form', 'data-toggle': 'modal', 'class': 'acceptConditions'})
            self.fields['accept_safety_form'].label = _("I hereby accept the Safety conditions on behalf of all visitors in my party.*")
        else:
            self.fields['accept_safety_form'].widget = forms.HiddenInput()

        if self.showing.activity.liability_tech_doc:
            self.fields['accept_disclaimer_form'].widget.attrs.update({
                'data-target': '#disclaimer_form', 'data-toggle': 'modal', 'class': 'acceptConditions'})
            self.fields['accept_disclaimer_form'].label = _("I hereby accept the Liability Disclaimer conditions on behalf of all visitors in my party.*")
        else:
            self.fields['accept_disclaimer_form'].widget = forms.HiddenInput()

        if self.showing.activity.conduct_tech_doc:
            self.fields['accept_conduct_form'].widget.attrs.update({
                'data-target': '#conduct_form', 'data-toggle': 'modal', 'class': 'acceptConditions'})
            self.fields['accept_conduct_form'].label = _("I hereby accept the Standard of Workplace Conduct conditions on behalf of all visitors in my party.*")
        else:
            self.fields['accept_conduct_form'].widget = forms.HiddenInput()

        if self.showing.activity.photo_release_form:
            self.fields['accept_photo_release_form'].widget.attrs.update({
                'data-target': '#photo_release_form', 'data-toggle': 'modal', 'class': 'acceptConditions'})
            self.fields['accept_photo_release_form'].label = _("I hereby accept the Photo and Publication Release Form on behalf of all visitors in my party.*")
        else:
            self.fields['accept_photo_release_form'].widget = forms.HiddenInput()
            
        # Setup crispyform
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        self.helper.add_input(Submit('submit', _('Submit')))

    def clean(self):

        cleaned_data = super(ReservationForm, self).clean()

        # Check e-mail
        email = cleaned_data.get('email')
        email_confirm = cleaned_data.get('email_confirm')

        if email and email_confirm:
            if email != email_confirm:
                raise forms.ValidationError(_('Email and Confirmation Email are different, please check!'))

        # Check if we already have the same reservation
        # res = Reservation.objects.filter(showing=self.showing, email=email, n_spaces=self.cleaned_data['n_spaces'])
        # if res:
        #     raise forms.ValidationError(_('This reservation already exists. In case of issues with your reservation, please send an email'))
        return cleaned_data

    def clean_n_spaces(self):
        n_spaces = self.cleaned_data['n_spaces']
        free_spaces = self.showing.free_spaces

        if n_spaces > self.showing.max_spaces_per_reservation:
            raise forms.ValidationError(
                _('The maximum number of spaces per person is '
                  '({max_spaces_per_reservation}).').format(
                    max_spaces_per_reservation=self.showing.max_spaces_per_reservation
                )
            )

        # Updating an existing reservation
        if self.instance.pk:
            old = Reservation.objects.filter(pk=self.instance.pk).first()

            if old and not old.is_waiting_list:
                # If user reduces or keeps same seats, always allowed
                if n_spaces <= old.n_spaces:
                    self.instance.is_waiting_list = False
                    return n_spaces

                # If user increases seats, must check real availability
                if n_spaces - old.n_spaces <= free_spaces:
                    self.instance.is_waiting_list = False
                    return n_spaces

                # No enough free seats, show clear error
                raise forms.ValidationError(
                    _("This exhibition is already fully booked, so we cannot increase the seats in your reservation. "
                      "If you need more seats, you can create a new reservation, but it will be added to the waiting list in case spots become available.")
                )

        # Creating a new reservation
        if n_spaces <= free_spaces:
            self.instance.is_waiting_list = False
            return n_spaces

        # Otherwise → try waiting list
        activity = self.showing.activity
        if not getattr(activity, "enable_waiting_list", False):
            self.add_error(
            None,  # None = error global del formulario
            forms.ValidationError(
                _("This activity is already fully booked and does not allow waiting list.")
            ))
            return n_spaces
        return self._validate_waiting_list(n_spaces)

    def _validate_waiting_list(self, n_spaces):
        current_reserved = (
            self.showing.reservation_set.aggregate(Sum("n_spaces"))["n_spaces__sum"] or 0
        )
        max_with_waiting = self.showing.total_spaces + int(self.showing.total_spaces * 0.5)

        if current_reserved + n_spaces > max_with_waiting:
            raise forms.ValidationError(
                _("The waiting list is already full (max {max} seats).").format(
                    max=max_with_waiting
                )
            )

        self.instance.is_waiting_list = True
        self.waiting_list_message = _(
            "⚠️ This is not a confirmed reservation. "
            "You will be added to the waiting list and contacted if a spot becomes available."
        )
        return n_spaces


class GroupReservationForm(forms.ModelForm):
    email_confirm = forms.EmailField(label=_('Confirm Email'))   
    location = forms.ModelChoiceField(
        queryset=Activity.objects.filter(group_enable=True),
        label=_('location'))
    guests = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = GroupReservation
        fields = ['name', 'phone', 'email', 'email_confirm', 'location', 'guests',
                  'accept_safety_form', 'accept_disclaimer_form']

    def __init__(self, *args, **kwargs):
        super(GroupReservationForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'nocopypaste'})
        self.fields['email_confirm'].widget.attrs.update({'class': 'nocopypaste'})

        self.fields['accept_safety_form'].label = _(
            "By checking this box I assert that I have read and agree to the Safety document on behalf of my party.*")

        self.fields['accept_safety_form'].widget.attrs.update({
            'data-form-field': 'accept_safety_form',
            'class': 'acceptConditions open-modal',
            'data-target': '#modal_form',
            'data-doc-type': 'safety'
        })

        self.fields['accept_disclaimer_form'].label = _(
            "By checking this box I affirm that I have read and agree to the Waiver and Release of Liability on behalf of my party.*")

        self.fields['accept_disclaimer_form'].widget.attrs.update({
            'data-form-field': 'accept_disclaimer_form',
            'class': 'acceptConditions open-modal',
            'data-target': '#modal_form',
            'data-doc-type': 'liability'
        })

    def clean_guests(self):
        guests = self.cleaned_data.get('guests')
        if guests:
            return guests
        return ''

    def clean_email_confirm(self):
        email = self.cleaned_data.get('email')
        email_confirm = self.cleaned_data.get('email_confirm')
        if email and email_confirm and email != email_confirm:
            raise forms.ValidationError(_('Email and Confirmation Email do not match.'))
        return email_confirm

