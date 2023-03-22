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

from django import forms
from django.utils.translation import gettext_lazy as _
from django.conf import Settings

from djangoplicity.visits.models import Reservation


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


class ReservationForm(forms.ModelForm):

    email_confirm = forms.EmailField(label=_('Confirm Email'))
    not_has_tested_positive_for_covid = forms.BooleanField(label=NOT_HAS_SYMPTOMS_LABEL,
                                                           required=False,
                                                           widget=forms.CheckboxInput(
                                                               attrs={
                                                                'class': 'acceptConditions covid'
                                                               })
                                                           )

    field_order = ['name', 'phone', 'alternative_phone', 'email',
                   'email_confirm', 'country', 'language', 'vehicle_plate', 'n_spaces',
                   'accept_safety_form', 'accept_disclaimer_form',
                   'accept_conduct_form']

    class Meta:
        model = Reservation
        exclude = ['code', 'created', 'last_modified']

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

        if self.showing.vehicle_plate_required:
            self.fields['vehicle_plate'].required = True

        self.fields['email'].widget.attrs.update({
            'class': 'nocopypaste'
        })
        self.fields['email_confirm'].widget.attrs.update({
            'class': 'nocopypaste'
        })

        self.fields['accept_safety_form'].widget.attrs.update({
            'data-target': '#safety_form', 'data-toggle': 'modal', 'class': 'acceptConditions'})
        self.fields['accept_safety_form'].label = _("I hereby accept the Safety conditions on behalf of all visitors in my party.*")

        self.fields['accept_disclaimer_form'].widget.attrs.update({
            'data-target': '#disclaimer_form', 'data-toggle': 'modal', 'class': 'acceptConditions'})
        self.fields['accept_disclaimer_form'].label = _("I hereby accept the Liability Disclaimer conditions on behalf of all visitors in my party.*")

        self.fields['accept_conduct_form'].widget.attrs.update({
            'data-target': '#conduct_form', 'data-toggle': 'modal', 'class': 'acceptConditions'})
        self.fields['accept_conduct_form'].label = _("I hereby accept the Standard of Workplace Conduct conditions on behalf of all visitors in my party.*")

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

        if n_spaces > self.showing.max_spaces_per_reservation:
            raise forms.ValidationError(_('The maximum number of spaces per person is '
                                          '({max_spaces_per_reservation}).').format(
                max_spaces_per_reservation=self.showing.max_spaces_per_reservation))

        if self.instance.pk:
            # Updating existing reservation
            if self.showing.free_spaces + self.instance.n_spaces - n_spaces < 0:
                raise forms.ValidationError(_('Only {number} spaces are '
                    'currently available').format(
                        number=self.instance.n_spaces))
        else:
            # Making new reservation
            if n_spaces > self.showing.free_spaces:
                raise forms.ValidationError(_('Only {number} spaces are '
                    'currently available').format(
                        number=self.showing.free_spaces))

        return n_spaces
