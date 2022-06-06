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
from __future__ import print_function
import os
import sys
from django.core.files.storage import FileSystemStorage
from django.core.validators import FileExtensionValidator
from hashids import Hashids
import html2text
from django.conf import settings
from django.core.mail import send_mail
from django.db import models, transaction
from django.db.models import Sum
from django.db.models.signals import post_delete, post_save
from django.template import loader
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.translation import gettext_lazy as _
from djangoplicity.archives.translation import TranslationProxyMixin
from djangoplicity.media.models import Image
from djangoplicity.metadata.archives import fields as metadatafields
from djangoplicity.translation.fields import TranslationForeignKey
from djangoplicity.translation.models import TranslationModel, translation_reverse
from django.contrib.sites.models import Site


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def handle_uploaded_file(instance, filename):
    """
    Generate a new name for an uploaded filed.

    Pattern used: <uuid>.<original extension>
    """
    dummy_base, ext = os.path.splitext(filename)
    import uuid
    name = "%s/%s%s" % ('visits', str(uuid.uuid1()), ext.lower())

    return name


class Activity(TranslationModel):
    id = metadatafields.AVMIdField(primary_key=True, verbose_name='ID',
        help_text='ID of the activity, also used in URLs')
    name = models.CharField(max_length=100)
    observatory = models.CharField(max_length=50)
    meeting_point = models.CharField(max_length=100)
    travel_info_url = models.URLField(help_text='Link to travel info page')
    map_url = models.URLField(help_text='Link to Google Maps')
    offered_languages = models.ManyToManyField('Language')
    duration = models.DurationField(help_text='Format: HH:MM')
    latest_reservation_time = models.IntegerField(default=24, help_text='Until how many hours before the start do we accept reservations')
    min_participants = models.IntegerField(help_text='Min. no of participants',
        default=5)
    max_participants = models.IntegerField(help_text='Max. no of participants',
        default=150)
    slogan = models.CharField(max_length=255, blank=True)
    description = metadatafields.AVMDescriptionField()
    published = models.BooleanField(default=False)

    safety_form_file = models.FileField(upload_to=handle_uploaded_file, blank=True, null=True,
                                        validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    disclaimer_form_file = models.FileField(upload_to=handle_uploaded_file, blank=True, null=True,
                                            validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    conduct_form_file = models.FileField(upload_to=handle_uploaded_file, blank=True, null=True,
                                         validators=[FileExtensionValidator(allowed_extensions=['pdf'])])

    key_visual_en = TranslationForeignKey(Image, blank=True, null=True,
        on_delete=models.SET_NULL, related_name='+',
        verbose_name='English poster')
    key_visual_es = TranslationForeignKey(Image, blank=True, null=True,
        on_delete=models.SET_NULL, related_name='+',
        verbose_name='Spanish poster')

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'activities'

    class Translation:
        excludes = []
        fields = ['name', 'meeting_point', 'slogan', 'description']

    def get_absolute_url(self):
        return translation_reverse('visits-showings-list', args=[str( self.id if self.is_source() else self.source.id )], lang=self.lang )


class ActivityProxy(Activity, TranslationProxyMixin):
    objects = Activity.translation_objects

    def clean(self):
        # Note: For some reason it's not possible to
        # to define clean/validate_unique in TranslationProxyMixin
        # so we have to do this trick, where we add the methods and
        # call into translation proxy mixin.
        self.id_clean()

    class Meta:
        proxy = True
        verbose_name = 'Activity translation'
        verbose_name_plural = 'Activity translations'


class Language(models.Model):
    code = models.CharField(primary_key=True, max_length=10)
    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Reservation(models.Model):
    code = models.CharField(max_length=50, blank=True)
    showing = models.ForeignKey('Showing')
    name = models.CharField(max_length=80, verbose_name=_('Full name'))
    phone = models.CharField(max_length=50, verbose_name=_('Phone'))
    alternative_phone = models.CharField(max_length=50, verbose_name=_('Alternative Phone'), blank=True, null=True)
    email = models.EmailField(verbose_name=_('Email'))
    country = models.CharField(max_length=50, verbose_name=_('Country'))
    language = models.ForeignKey(Language, verbose_name=_('Preferred language'))
    n_spaces = models.SmallIntegerField(verbose_name=_('Number of '
        'places'))
    created = models.DateTimeField(default=timezone.now)
    last_modified = models.DateTimeField(default=timezone.now)

    accept_safety_form = models.BooleanField(verbose_name=_('Accept Safety Form'), default=False)
    accept_disclaimer_form = models.BooleanField(verbose_name=_('Accept Disclaimer Form'), default=False)
    accept_conduct_form = models.BooleanField(verbose_name=_('Accept Conduct Form'), default=False)

    def __unicode__(self):
        return '{}, {} ({} spaces)'.format(self.email, self.showing,
            self.n_spaces)

    @classmethod
    def delete_notification(cls, sender, instance, **kwargs):
        transaction.on_commit(instance.showing.update_spaces_count)

    def get_absolute_url(self):
        return reverse('visits-reservation-update', args=[self.code])

    def save(self, **kwargs):
        self.last_modified = timezone.now()
        super(Reservation, self).save(**kwargs)
        transaction.on_commit(self.showing.update_spaces_count)

    def get_context(self):
        return {
            'base_url': "{}://{}".format(getattr(settings, "URLS_SCHEME", "https"), Site.objects.get_current().domain),
            'MEDIA_URL': settings.MEDIA_URL,
            'STATIC_URL': settings.STATIC_URL,
            'reservation': self,
            'home': 'http://%s' % Site.objects.get_current().domain,
        }

    def send_confirmation_email(self):
        template = loader.get_template('visits/emails/reservation-confirm.html')
        translation.activate(self.language.code)

        html_message = template.render(self.get_context())
        txt_message = html2text.html2text(html_message)

        #  print('DEBUG')
        #  print(_('Reservation confirmation'))
        #  print(html_message)
        #  print('DEBUG')

        send_mail(
            _('Reservation confirmation'),
            txt_message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            html_message=html_message,
        )

        translation.deactivate()

    def send_reminder_email(self):
        template = loader.get_template('visits/emails/reservation-reminder.html')

        translation.activate(self.language.code)

        html_message = template.render(self.get_context())
        txt_message = html2text.html2text(html_message)

        #  print('DEBUG')
        #  print(_('Reservation reminder'))
        #  print(html_message)
        #  print('DEBUG')

        send_mail(
            _('Reservation reminder'),
            txt_message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            html_message=html_message,
        )

        translation.deactivate()

    def send_deleted_email(self):
        template = loader.get_template('visits/emails/reservation-deleted.html')

        translation.activate(self.language.code)

        html_message = template.render(self.get_context())
        txt_message = html2text.html2text(html_message)

        send_mail(
            _('Reservation deleted'),
            txt_message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            html_message=html_message,
        )

        translation.deactivate()

    def send_updated_email(self):
        template = loader.get_template('visits/emails/reservation-updated.html')

        translation.activate(self.language.code)

        html_message = template.render(self.get_context())
        txt_message = html2text.html2text(html_message)

        send_mail(
            _('Reservation updated'),
            txt_message,
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            html_message=html_message,
        )

        translation.deactivate()


class Showing(models.Model):
    activity = TranslationForeignKey('Activity', related_name='showings')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(blank=True, null=True,
        help_text='If left empty will be calculated from the activity '
        'duration')
    private = models.BooleanField(default=False,
        help_text='Whether the showing if private.')
    offered_languages = models.ManyToManyField('Language')
    max_spaces_per_reservation = models.SmallIntegerField(default=0,
        help_text='Maximum number of spaces per reservation, 0 for no maximum')

    total_spaces = models.IntegerField(help_text='Total number of seats '
        '(based on selected activity)', blank=True)
    free_spaces = models.IntegerField(help_text='Current number of available '
        'seats (based on current resevations)', blank=True)

    def __unicode__(self):
        return '{} — {}'.format(
            self.activity,
            self.start_time.strftime('%Y-%m-%d %H:%M'),
        )

    def get_absolute_url(self):
        return reverse('visits-reservation-create', args=[self.pk])

    def get_report_url(self):
        return reverse('visits-showings-reports-detail', args=[self.pk])

    def get_activity(self):
        '''
        Return the activity in the current language
        '''
        return Activity.objects.fallback(translation.get_language()).filter(
            pk=self.activity.pk).get()

    def save(self, **kwargs):
        if self.total_spaces is None:
            self.total_spaces = self.activity.max_participants

        if self.free_spaces is None:
            self.free_spaces = self.total_spaces

        if not self.end_time:
            self.end_time = self.start_time + self.activity.duration

        super(Showing, self).save(**kwargs)
        transaction.on_commit(self.update_spaces_count)

    def update_spaces_count(self):
        '''
        Update the number of free_seats, called in Reservation.save()
        '''
        reserved_spaces = self.reservation_set.aggregate(
            Sum('n_spaces')
        )['n_spaces__sum'] or 0
        free_spaces = self.total_spaces - reserved_spaces

        # We use "update" so as not to trigger signals
        Showing.objects.filter(pk=self.pk).update(free_spaces=free_spaces)


def generate_code(sender, instance, raw, **kwargs):
    '''
    Done as signal in post_save as the PK used is assigned by the DB after
    the save
    '''
    if raw:
        return

    if instance.code == '':
        # Generate code
        hashids = Hashids(alphabet=settings.HASHIDS_ALPHABET,
            salt=settings.HASHIDS_SALT, min_length=5)
        instance.code = hashids.encrypt(instance.pk)
        instance.save()

post_save.connect(generate_code, sender=Reservation)
post_delete.connect(Reservation.delete_notification, sender=Reservation)
