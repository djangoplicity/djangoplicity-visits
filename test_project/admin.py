# -*- coding: utf-8 -*-
# Import all admin interfaces we need
import django.contrib.sites.admin
from djangoplicity.contrib.admin.discover import autoregister
from djangoplicity.contrib.admin.sites import AdminSite

import djangoplicity.visits.admin

# Register each applications admin interfaces with
# an admin site.
admin_site = AdminSite(name="admin_site")
adminlogs_site = AdminSite(name="adminlogs_site")

autoregister(admin_site, django.contrib.auth.admin)
autoregister(admin_site, django.contrib.sites.admin)

autoregister(admin_site, djangoplicity.visits.admin)


admin_site.register(django.contrib.auth.models.User, django.contrib.auth.admin.UserAdmin)

admin_site.register(django.contrib.auth.models.Group, django.contrib.auth.admin.GroupAdmin)
