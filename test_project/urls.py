"""test_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from test_project.admin import adminlogs_site
from test_project.admin import admin_site
from django.conf import settings


urlpatterns = [
    url(r'^admin/', admin_site.urls),
    url(r'^admin/cache/', include(('djangoplicity.cache.urls', "cache"), namespace="admincache_site")),
    url(r'^admin/system/', adminlogs_site.urls, {'extra_context': {'ADMINLOGS_SITE': True}}),
    url(r'^admin/history/', include(('djangoplicity.adminhistory.urls', "history"), namespace="adminhistory_site")),
    url(r'^tinymce/', include('tinymce.urls')),
    # djangoplicty visits
    url(r'^visits/', include('djangoplicity.visits.urls'), {'translate': True}),
]

if settings.DEBUG_TOOLBAR:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
