from django.conf.urls import patterns, include, url
from django.contrib.auth.views import login, logout
from django.views.generic import ListView
from qsub.views import *
from qsub.models import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'QuEST.views.home', name='home'),
    # url(r'^QuEST/', include('QuEST.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    (r'^main/$', main),
    (r'^$', main),
    (r'^register/$', register),
    (r'^accounts/login/$', login),
    (r'^accounts/logout/$', logout),
    (r'^tournaments/$', tournaments),
    (r'^create_tournament/$', create_tournament)
)
