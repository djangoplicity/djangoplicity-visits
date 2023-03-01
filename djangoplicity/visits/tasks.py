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

    reservations = []
    days_reminder = getattr(settings, 'SEND_RESERVATION_REMINDER_IN_DAYS', 1)

    if days_reminder > 1:
        # Get reservations that start within a specified day
        day_to_start = date.today() + timedelta(days=days_reminder)
        reservations = Reservation.objects.filter(
            showing__start_time__date=day_to_start
        )
    elif days_reminder == 1:
        # Get reservations starting tomorrow
        tomorrow = date.today() + timedelta(days=days_reminder)
        reservations = Reservation.objects.filter(
            showing__start_time__date=tomorrow
        )

    # Get the reservations that were modified yesterday
    yesterday = date.today() - timedelta(days=1)
    reservations_yesterday = Reservation.objects.filter(
        last_modified__date=yesterday
    )

    for reservation in reservations:
        reservation.send_reminder_email()
    for reservation in reservations_yesterday:
        reservation.send_reminder_email()
