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
    (r'^tour/$', tour),
    (r'^school/$', school),
    (r'^schoolinfo/(?P<school_id>\d+)/$', school_info),
    (r'^schooladd/$', create_school),
    (r'^team/$', team),
    (r'^touradd/$', create_tournament),
    (r'^teamadd/$', create_team),
    (r'^touredit/(?P<tour_id>\d+)/$', edit_tournament),
    (r'^teamedit/(?P<team_id>\d+)/$', edit_team),
    (r'^find_player/$', find_player),
    (r'^find_teammate/$', find_teammate),
    (r'^removeteammate/(?P<team_id>\d+)/(?P<teammate_id>\d+)/$', remove_teammate),
    (r'^removeeditor/(?P<tournament_id>\d+)/(?P<editor_id>\d+)/$', remove_editor),
    (r'^roleassign/(?P<editor_id>\d+)/(?P<tour_id>\d+)/$', role_assign),
    (r'^writeassign/(?P<writer_id>\d+)/(?P<team_id>\d+)/$', team_role_assign),
    (r'^packet/$', packet),
    (r'^distributions/$', distributions),
    (r'^editdistribution/(?P<dist_id>\d+)/$', edit_distribution),
    (r'^editdistribution/$', edit_distribution),
    (r'^packetcreate/(?P<team_id>\d+)/$', create_packet),
    (r'^packetedit/(?P<packet_id>\d+)/$', edit_packet),
    (r'^edittossups/(?P<packet_id>\d+)/$', edit_tossups),
    #(r'^edittossup/(?P<tossup_id>\d+)/$', edit_tossup),
    (r'^bonusedit/(?P<packet_id>\d+)/$', edit_bonuses),
    #(r'^addtossup/(?P<packet_id>\d+)/$', add_tossup),
    #(r'^addbonus/(?P<packet_id>\d+)/$', add_bonus),
    (r'^addquestion/(?P<type>\w+)/(?P<packet_id>\d+)/$', add_question),
    (r'^editquestion/(?P<type>\w+)/(?P<question_id>\d+)/$', edit_question),
    (r'^questionview/(?P<type>\w+)/(?P<packet_id>\d+)/$', question_view),
#     ListView.as_view(queryset=Tournament.objects.order_by('-date')[:5],
#                                  context_object_name='tournament_list',
#                                  template_name='tourview.html' )),
    (r'^register/$', register),
    (r'^accounts/login/$', login),
    (r'^accounts/logout/$', logout),
)
