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


from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from djangoplicity.visits.views import (
    ReservationCreateView, ReservationDeleteView, ReservationConfirmView,
    ReservationDeleteConfirmView, ReservationUpdateView, ShowingListView,
    ShowingReportDetailView, ShowingReportListView, ReservationCancelView
)

urlpatterns = [
    url(r'^reports/$', login_required(ShowingReportListView.as_view()),
        name='visits-showings-reports-list'),
    url(r'^reports/(?P<pk>[-\w]+)/$', login_required(
        ShowingReportDetailView.as_view()),
        name='visits-showings-reports-detail'),
    url(r'^delete/(?P<code>[-\w]+)/$', ReservationDeleteView.as_view(),
        name='visits-reservation-delete'),
    url(r'^confirmed/(?P<code>[-\w]+)/$', ReservationConfirmView.as_view(),
        name='visits-reservation-confirm'),
    url(r'^reservation-cancelled/$', ReservationDeleteConfirmView.as_view(),
        name='visits-reservation-delete-confirm'),
    url(r'^update/(?P<code>[-\w]+)/$', ReservationUpdateView.as_view(),
        name='visits-reservation-update'),
    url(r'^cancel/(?P<code>[-\w]+)/$', ReservationCancelView.as_view(),
        name='visits-reservation-cancel'),
    url(r'^booking/(?P<showingpk>[-\w]+)/$', ReservationCreateView.as_view(),
        name='visits-reservation-create'),
    url(r'^(?P<pk>[-\w]+)/$', ShowingListView.as_view(),
        name='visits-showings-list'),
]
