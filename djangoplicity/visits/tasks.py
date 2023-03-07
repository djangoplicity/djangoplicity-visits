# -*- coding: utf-8 -*-


from __future__ import unicode_literals
from datetime import datetime, date, timedelta
import pytz

from django.conf import settings
from celery.task import task
from celery.utils.log import get_task_logger

from djangoplicity.visits.models import Reservation


logger = get_task_logger(__name__)


@task
def reservation_reminder():
    """
    Send a reminder for all visits happening the next day
    Send a reminder for all visits the day after last modification
    """

    # Only in prod
    if settings.SITE_ENVIRONMENT != 'prod':
        return

    if not getattr(settings, 'DP_VISITS_SEND_REMINDERS', True):
        return

    tomorrow = date.today() + timedelta(days=1)
    yesterday = date.today() - timedelta(days=1)

    reservations_tomorrow = Reservation.objects.filter(
        showing__start_time__date=tomorrow
    )
    reservations_yesterday = Reservation.objects.filter(
        last_modified__date=yesterday
    )

    for reservation in reservations_tomorrow:
        reservation.send_reminder_email()
    for reservation in reservations_yesterday:
        reservation.send_reminder_email()
