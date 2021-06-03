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

from djangoplicity.visits.models import Reservation


class ReservationForm(forms.ModelForm):

    email_confirm = forms.EmailField(label=_('Confirm Email'))

    field_order = ['name', 'phone', 'alternative_phone', 'email', 'email_confirm', 'country', 'language', 'n_spaces']
    
    class Meta:
        model = Reservation
        exclude = ['code', 'created', 'last_modified']

    def __init__(self, *args, **kwargs):
        self.showing = kwargs.pop('showing', None)

        super(ReservationForm, self).__init__(*args, **kwargs)

        if self.showing is None:
            self.showing = self.instance.showing

        self.fields['showing'].widget = forms.HiddenInput()

        max_value = self.showing.max_spaces_per_reservation
        if max_value == 0:
            max_value = self.showing.free_spaces

        # If we're editing an existing showing then max_value is max_value
        # added to the currently selected places
        if self.instance.pk:
            max_value += self.instance.n_spaces

        self.fields['n_spaces'] = forms.IntegerField(
            label = self.fields['n_spaces'].label,
            min_value=1,
            max_value=max_value,
        )

        self.fields['email'].widget.attrs.update({
            'class': 'nocopypaste'
        })
        self.fields['email_confirm'].widget.attrs.update({
            'class': 'nocopypaste'
        })

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
        res = Reservation.objects.filter(showing=self.showing, email=email, n_spaces=self.cleaned_data['n_spaces'])
        if res:
            raise forms.ValidationError(_('This reservation already exists. In case of issues with your reservation, please send an email to <a href="visits@eso.org">visits@eso.org</a>.'))

        return cleaned_data

    def clean_n_spaces(self):
        n_spaces = self.cleaned_data['n_spaces']

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
