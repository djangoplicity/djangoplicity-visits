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

from djangoplicity.contrib import admin as dpadmin

from djangoplicity.visits.models import Activity, ActivityProxy,\
    Language, Reservation, Showing


class ActivityAdmin(dpadmin.DjangoplicityModelAdmin):
    filter_horizontal = ('offered_languages', )
    list_display = ('id', 'name')
    raw_id_fields = ('key_visual_en', 'key_visual_es')

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['id']
        else:
            return []


class ActivityProxyAdmin(dpadmin.DjangoplicityModelAdmin):
    fields = ('lang', 'source', 'translation_ready', 'name', 'meeting_point',
        'slogan', 'description')
    list_display = ('pk', 'name')
    raw_id_fields = ('source', )


class ReservationAdmin(dpadmin.DjangoplicityModelAdmin):
    list_display = ('email', 'name', 'showing', 'n_spaces', 'created')
    ordering = ['showing__start_time']
    raw_id_fields = ('showing', )
    readonly_fields = ('code', 'created', 'last_modified')
    search_fields = ('email', 'name')


class ShowingAdmin(dpadmin.DjangoplicityModelAdmin):
    filter_horizontal = ('offered_languages', )
    list_display = ('activity', 'start_time', 'private', 'total_spaces',
        'free_spaces')
    list_filter = ('activity', 'private')
    readonly_fields = ('total_spaces', 'free_spaces')


def register_with_admin(admin_site):
    admin_site.register(Activity, ActivityAdmin)
    admin_site.register(ActivityProxy, ActivityProxyAdmin)
    admin_site.register(Language)
    admin_site.register(Reservation, ReservationAdmin)
    admin_site.register(Showing, ShowingAdmin)


register_with_admin(admin.site)
