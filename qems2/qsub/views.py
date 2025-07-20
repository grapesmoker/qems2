import json
import csv
import unicodecsv
import time
import datetime
import sys

from django.template import RequestContext
from django.shortcuts import render_to_response
from django.forms.formsets import formset_factory
from django.http import HttpResponse, HttpResponseRedirect

from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from models import *
from forms import *
from qems2.qsub.model_utils import *
from utils import *
from packet_parser import parse_packet_data
from django.utils.safestring import mark_safe
from haystack.query import SearchQuerySet
from django_comments.models import Comment
from django.db.models import Q
from django.core.cache import cache

from django.contrib.contenttypes.models import ContentType


@login_required
def main (request):
    return question_sets(request)

@login_required
def sidebar (request):
    writer = request.user.writer
    # the tournaments for which this user is a writer
    writer_sets = writer.question_set_writer.all()
    # all the tournaments owned by this user
    owned_sets = QuestionSet.objects.filter(owner=writer)
    # the tournaments for which this user is an editor
    editor_sets = writer.question_set_editor.all()

    all_sets = editor_sets
    print 'All sets object:'
    print all_sets
        
    return render_to_response('sidebar.html', {'question_sets': all_sets, 'user': writer},
           context_instance=RequestContext(request))

@login_required
def question_sets (request):
    writer = request.user.writer

    # all the tournaments owned by this user
    owned_sets = QuestionSet.objects.filter(owner=writer)
    # the tournaments for which this user is an editor
    editor_sets = writer.question_set_editor.all()
    
    all_sets = owned_sets | editor_sets | writer.question_set_writer.all()
    all_sets = all_sets.order_by('date')
    
    # Sets that are in the future
    upcoming_sets = {}
    
    # Sets that are in the past
    completed_sets = {}
        
    for qset in (all_sets):
        if (qset.date >= datetime.now().date()):
            upcoming_sets[qset.id] = qset
        else:
            completed_sets[qset.id] = qset
            
    upcoming_sets = upcoming_sets
    completed_sets = completed_sets
            
    upcoming_sets = upcoming_sets.values()
    completed_sets = completed_sets.values()
    
    upcoming_sets = sorted(upcoming_sets, key=lambda qset: qset.date)
    completed_sets = sorted(completed_sets, key=lambda qset: qset.date)

    all_sets  = [{'header': 'Upcoming question sets', 'qsets': upcoming_sets, 'id': 'qsets-write'},
                 {'header': 'Completed question sets', 'qsets': completed_sets, 'id': 'qsets-complete'}]

    print all_sets
    return render_to_response('question_sets.html', {'question_set_list': all_sets, 'user': writer},
                              context_instance=RequestContext(request))

def packet(request):
    if request.user.is_authenticated():
        player = request.user.get_profile()
        packets = player.packet_set.filter(date_submitted=None)

        print 'packets: ', packets

        return render_to_response('packetview.html',
                                  {'packet_list': packets},
                                  context_instance=RequestContext(request))

    else:
        return HttpResponseRedirect('/accounts/login/')

@login_required
def create_question_set (request):
    user = request.user.writer

    if request.method == 'POST':
        form = QuestionSetForm(data=request.POST)
        if form.is_valid():
            # for the moment, just use the default ACF Distribution
            #dist = Distribution.objects.get(id=1)
            question_set = form.save(commit=False)
            question_set.owner = user
            question_set.editors = []
            question_set.editors.append(user)
            #question_set.distribution = dist
            question_set.save()
            form.save_m2m()
            user.question_set_editor.add(question_set)
            user.save()

            dist = question_set.distribution
            dist_entries = dist.distributionentry_set.all()
            for entry in dist_entries:
                set_wide_entry = SetWideDistributionEntry()
                set_wide_entry.num_bonuses = question_set.num_packets * entry.min_tossups
                set_wide_entry.num_tossups = question_set.num_packets * entry.min_bonuses
                set_wide_entry.question_set = question_set
                set_wide_entry.dist_entry = entry
                set_wide_entry.save()

                tiebreak_entry = TieBreakDistributionEntry()
                tiebreak_entry.num_bonuses = 1
                tiebreak_entry.num_tossups = 1
                tiebreak_entry.question_set = question_set
                tiebreak_entry.dist_entry = entry
                tiebreak_entry.save()

            set_distro_formset = create_set_distro_formset(question_set)
            tiebreak_formset = create_tiebreak_formset(question_set)
            comment_tab_list = []

            return render_to_response('edit_question_set.html',
                                      {'message': 'Your question set has been successfully created!',
                                       'message_class': 'alert-box success',
                                       'qset': question_set,
                                       'user': user,
                                       'form': form,
                                       'set_distro_formset': set_distro_formset,
                                       'tiebreak_formset': tiebreak_formset,
                                       'editors': [ed for ed in question_set.editor.all() if ed != question_set.owner],
                                       'writers': question_set.writer.all(),
                                       'tossups': Tossup.objects.filter(question_set=question_set),
                                       'bonuses': Bonus.objects.filter(question_set=question_set),
                                       'comment_tab_list': comment_tab_list,
                                       'packets': question_set.packet_set.all(),},
                                      context_instance=RequestContext(request))
        else:
            print form.errors
            distributions = Distribution.objects.all()
            return render_to_response('create_question_set.html',
                                      {'message': 'There was an error in creating your question set!',
                                       'message_class': 'alert-box warning',
                                       'form': form,
                                       'distributions': distributions,
                                       'user': user},
                                      context_instance=RequestContext(request))
    else:
        form = QuestionSetForm()
        distributions = Distribution.objects.all()

    return render_to_response('create_question_set.html',
                              {'form': form,
                               'distributions': distributions,
                               'user': user},
                              context_instance=RequestContext(request))

@login_required
def edit_question_set(request, qset_id):
    read_only = False
    message = ''
    tossups = []
    bonuses = []
    
    qset = QuestionSet.objects.get(id=qset_id)
    qset_editors = qset.editor.all()
    qset_writers = qset.writer.all()
    user = request.user.writer
    set_status = {}
    set_distro_formset = None
    tiebreak_formset = None
    writer_stats = {}

    total_tu_req = 0
    total_bs_req = 0
    total_tu_written = 0
    total_bs_written = 0
    comment_tab_list = []
    tu_needed = 0
    bs_needed = 0
    set_pct_complete = 0

    role = get_role_no_owner(user, qset)

    if user != qset.owner and user not in qset_editors and user not in qset_writers:
        messages.error(request, 'You are not authorized to view information about this tournament!')
        return HttpResponseRedirect('/failure.html/')

    if request.method == 'POST':        
        if (user == qset.owner or user in qset_editors):
            form = QuestionSetForm(data=request.POST)
            if form.is_valid():
                qset = QuestionSet.objects.get(id=qset_id)
                qset.name = form.cleaned_data['name']
                qset.date = form.cleaned_data['date']
                qset.distribution = form.cleaned_data['distribution']
                qset.num_packets = form.cleaned_data['num_packets']
                qset.char_count_ignores_pronunciation_guides = form.cleaned_data['char_count_ignores_pronunciation_guides']
                qset.max_acf_tossup_length = form.cleaned_data['max_acf_tossup_length']
                qset.max_acf_bonus_length = form.cleaned_data['max_acf_bonus_length']
                qset.max_vhsl_bonus_length = form.cleaned_data['max_vhsl_bonus_length']
                qset.save()
                cache.clear()

                tossups, tossup_dict, bonuses, bonus_dict = get_tossup_and_bonuses_in_set(qset, question_limit=30, preview_only=True)

                if user == qset.owner:
                    read_only = False
                else:
                    read_only = True

                set_status, total_tu_req, total_bs_req, tu_needed, bs_needed, set_pct_complete = get_questions_remaining(qset)
                writer_stats = get_writer_questions_remaining(qset, total_tu_req, total_bs_req)
                                                                
                comment_tab_list = get_comment_tab_list(tossup_dict, bonus_dict)

                return render_to_response('edit_question_set.html',
                                          {'form': form,
                                           'qset': qset,
                                           'user': user,
                                           'editors': [ed for ed in qset_editors if ed != qset.owner],
                                           'writers': qset.writer.all(),
                                           'writer_stats': writer_stats,
                                           'upload_form': QuestionUploadForm(),
                                           'set_status': set_status,
                                           'set_pct_complete': '{0:0.2f}%'.format(set_pct_complete),
                                           'set_pct_progress_bar': '{0:0.0f}%'.format(set_pct_complete),
                                           'tu_needed': tu_needed,
                                           'bs_needed': bs_needed,
                                           'tossups': tossups,
                                           'bonuses': bonuses,
                                           'packets': qset.packet_set.all(),
                                           'comment_list': comment_tab_list,
                                           'role': role,
                                           'message': 'Your changes have been successfully saved.',
                                           'message_class': 'alert-success'},
                                          context_instance=RequestContext(request))
            else:
                qset_editors = []
        else:
            render_to_response('failure.html', {'message': 'You are not authorized to change this set!'})
    else:
        print "Begin edit_question_set get", time.strftime("%H:%M:%S")
        if user not in qset_editors and user != qset.owner and user not in qset.writer.all():
            # Just redirect to main in this case of no permissions
            # TODO: a better story
            return HttpResponseRedirect('/main.html')

        tossups, tossup_dict, bonuses, bonus_dict = get_tossup_and_bonuses_in_set(qset, question_limit=30, preview_only=True)
        
        if user not in qset_editors and user != qset.owner:
            form = QuestionSetForm(instance=qset, read_only=True)
            read_only = True
            message = ''
        else:
            if user == qset.owner:
                read_only = False
            elif user in qset.writer.all() or user in qset.editor.all():
                read_only = True
            form = QuestionSetForm(instance=qset)

        set_status, total_tu_req, total_bs_req, tu_needed, bs_needed, set_pct_complete = get_questions_remaining(qset)
        writer_stats = get_writer_questions_remaining(qset, total_tu_req, total_bs_req)
                                                                
        comment_tab_list = get_comment_tab_list(tossup_dict, bonus_dict)                    

    print "End edit_question_set get", time.strftime("%H:%M:%S")
        
    return render_to_response('edit_question_set.html',
                              {'form': form,
                               'user': user,
                               'editors': [ed for ed in qset_editors if ed != qset.owner],
                               'writers': [wr for wr in qset_writers if wr != qset.owner],
                               'writer_stats': writer_stats,
                               'set_status': set_status,
                               'set_pct_complete': '{0:0.2f}%'.format(set_pct_complete),
                               'set_pct_progress_bar': '{0:0.0f}%'.format(set_pct_complete),
                               'tu_needed': tu_needed,
                               'bs_needed': bs_needed,
                               'upload_form': QuestionUploadForm(),
                               'tossups': tossups,
                               'bonuses': bonuses,
                               'packets': qset.packet_set.all(),
                               'comment_tab_list': comment_tab_list,
                               'qset': qset,
                               'role': role,
                               'read_only': read_only,
                               'message': message},
                              context_instance=RequestContext(request))

@login_required
def categories(request, qset_id, category_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    qset_editors = qset.editor.all()
    qset_writers = qset.writer.all()

    category_object = DistributionEntry.objects.get(id=category_id)

    entry = qset.setwidedistributionentry_set.get(dist_entry=category_object)
    tu_required = entry.num_tossups
    bs_required = entry.num_bonuses
    tu_written = qset.tossup_set.filter(category=entry.dist_entry).count()
    bs_written = qset.bonus_set.filter(category=entry.dist_entry).count()

    category_status =   {'tu_req': tu_required,
                         'tu_in_cat': tu_written,
                         'bs_req': bs_required,
                         'bs_in_cat': bs_written
                         }

    message = category_object.category
    tossups = []
    bonuses = []
    if user not in qset_editors and user != qset.owner and user not in qset.writer.all():
        message = 'You are not authorized to view this set'
    else:
        tossups = Tossup.objects.filter(question_set=qset).filter(category=category_id)
        bonuses = Bonus.objects.filter(question_set=qset).filter(category=category_id)
            
    return render_to_response('categories.html',
        {
        'user': user,
        'tossups': tossups,
        'bonuses': bonuses,
        'category_status': category_status,
        'qset': qset,
        'message': message,
        'category': category_object},
        context_instance=RequestContext(request))	

@login_required
def view_all_questions(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    qset_editors = qset.editor.all()
    qset_writers = qset.writer.all()

    message = ''
    tossups = []
    bonuses = []
    if user not in qset_editors and user != qset.owner and user not in qset.writer.all():
        message = 'You are not authorized to view this set'
        return render_to_response('failure.html',
                                 {'message': message,
                                  'message_class': 'alert-box alert'},
                                  context_instance=RequestContext(request))        
    else:
        tossups, tossup_dict, bonuses, bonus_dict = get_tossup_and_bonuses_in_set(qset, question_limit=10000, preview_only=True)
            
    return render_to_response('view_all_questions.html',
        {
        'user': user,
        'tossups': tossups,
        'bonuses': bonuses,
        'qset': qset,
        'message': message},
        context_instance=RequestContext(request))	

@login_required
def view_all_comments(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    qset_editors = qset.editor.all()
    qset_writers = qset.writer.all()

    message = ''
    tossups = []
    bonuses = []
    if user not in qset_editors and user != qset.owner and user not in qset.writer.all():
        message = 'You are not authorized to view this set'
        return render_to_response('failure.html',
                                 {'message': message,
                                  'message_class': 'alert-box alert'},
                                  context_instance=RequestContext(request))        
    else:
        tossups, tossup_dict, bonuses, bonus_dict = get_tossup_and_bonuses_in_set(qset, question_limit=10000, preview_only=True)
        comment_tab_list = get_comment_tab_list(tossup_dict, bonus_dict, comment_limit=10000)
            
    return render_to_response('view_all_comments.html',
        {
        'user': user,
        'comment_tab_list': comment_tab_list,
        'qset': qset,
        'message': message},
        context_instance=RequestContext(request))	

@login_required
def question_set_distribution(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    qset_editors = qset.editor.all()
    qset_writers = qset.writer.all()
    set_distro_formset = []
    tiebreak_formset = []
    read_only = True

    message = ''
    if user not in qset_editors and user != qset.owner and user not in qset.writer.all():
        message = 'You are not authorized to view this set'
        return render_to_response('failure.html',
                                 {'message': message,
                                  'message_class': 'alert-box alert'},
                                  context_instance=RequestContext(request))                
    elif user == qset.owner:
        set_distro_formset = create_set_distro_formset(qset)
        tiebreak_formset = create_tiebreak_formset(qset)    
        read_only = False
    else:
        set_distro_formset = create_set_distro_formset(qset)
        tiebreak_formset = create_tiebreak_formset(qset)        
            
    return render_to_response('question_set_distribution.html',
        {
        'user': user,
        'set_distro_formset': set_distro_formset,
        'tiebreak_formset': tiebreak_formset,
        'qset': qset,
        'message': message,
        'read_only': read_only},
        context_instance=RequestContext(request))	

@login_required
def edit_set_distribution(request, qset_id):

    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)

    if request.method == 'POST':

        DistributionEntryFormset = formset_factory(SetWideDistributionEntryForm, can_delete=False, extra=0)
        formset = DistributionEntryFormset(data=request.POST, prefix='distentry')

        if formset.is_valid() and user == qset.owner:
            for dist_form in formset.forms:
                entry_id = int(dist_form.cleaned_data['entry_id'])
                num_tossups = int(dist_form.cleaned_data['num_tossups'])
                num_bonuses = int(dist_form.cleaned_data['num_bonuses'])

                entry = SetWideDistributionEntry.objects.get(id=entry_id)
                entry.num_tossups = num_tossups
                entry.num_bonuses = num_bonuses
                entry.save()

            return HttpResponseRedirect('/question_set_distribution/{0}'.format(qset_id))
        else:
            return render_to_response('failure.html',
                                     {'message': 'Something went wrong. We\'re working on it.',
                                      'message_class': 'alert-box alert'},
                                      context_instance=RequestContext(request))
    elif request.method == 'GET':
        if user == qset.owner:
            return render_to_response('view_all_questions.html',
                {
                'user': user,
                'tossups': tossups,
                'bonuses': bonuses,
                'qset': qset,
                'message': message},
                context_instance=RequestContext(request))	
            

@login_required
def edit_set_tiebreak(request, qset_id):

    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)

    if request.method == 'POST':

        TiebreakDistributionEntryFormset = formset_factory(TieBreakDistributionEntryForm, can_delete=False, extra=0)
        formset = TiebreakDistributionEntryFormset(data=request.POST, prefix='tiebreak')

        if formset.is_valid() and user == qset.owner:
            for dist_form in formset.forms:
                entry_id = int(dist_form.cleaned_data['entry_id'])
                num_tossups = int(dist_form.cleaned_data['num_tossups'])
                num_bonuses = int(dist_form.cleaned_data['num_bonuses'])

                entry = TieBreakDistributionEntry.objects.get(id=entry_id)
                entry.num_tossups = num_tossups
                entry.num_bonuses = num_bonuses
                entry.save()

            return HttpResponseRedirect('/question_set_distribution/{0}'.format(qset_id))
        else:
            return render_to_response('failure.html',
                                     {'message': 'Something went wrong. We\'re working on it.',
                                      'message_class': 'alert-box alert'},
                                      context_instance=RequestContext(request))

@login_required
def find_editor(request):
    pass

@login_required
def add_editor(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    message = ''

    if request.method == 'GET':
        if user == qset.owner:
            current_editors = qset.editor.all()

            available_editors = [writer for writer in Writer.objects.all().order_by('user__last_name', 'user__first_name', 'user__username') #exclude(is_active=False)
                                 if writer not in current_editors and
                                    writer is not qset.owner and writer.id != 1
                                    and writer.user.is_active]
        else:
            available_editors = []
            return render_to_response('failure.html',
                                     {'message': 'You are not authorized to make changes to this tournament!',
                                      'message_class': 'alert-box alert'},
                                      context_instance=RequestContext(request))

        return render_to_response('add_editor.html',
                                 {'qset': qset,
                                  'available_editors': available_editors,
                                  'message': message,
                                  'user': user},
                                  context_instance=RequestContext(request))


    elif request.method == 'POST':
        if user == qset.owner:
            editors_to_add = request.POST.getlist('editors_to_add')
            # do some basic validation here
            if all([x.isdigit() for x in editors_to_add]):
                for editor_id in editors_to_add:
                    editor = Writer.objects.get(id=editor_id)
                    qset.editor.add(editor)

                    # Don't have someone be both a writer and editor--delete them
                    try:
                        writer = qset.writer.get(id=editor_id)
                        if (writer is not None):
                            qset.writer.remove(writer)
                    except:
                        print "No writer to delete" # TODO: Come up with a better way of handling this

                qset.save()
                cache.clear()
                set_editors = qset.editor.all()
                available_editors = [writer for writer in Writer.objects.all().order_by('user__last_name', 'user__first_name', 'user__username') #exclude(is_active=False)
                                     if writer not in set_editors and
                                        writer is not qset.owner and writer.id != 1
                                        and writer.user.is_active]
            else:
                message = 'Invalid data entered!'
                available_editors = []
        else:
            available_editors = []
            return render_to_response('failure.html',
                                     {'message': 'You are not authorized to make changes to this tournament!',
                                      'message_class': 'alert-box alert'},
                                      context_instance=RequestContext(request))

        return render_to_response('add_editor.html',
                                 {'qset': qset,
                                  'available_editors': available_editors,
                                  'message': message,
                                  'user': user},
                                  context_instance=RequestContext(request))

@login_required
def add_writer(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    message = ''
    message_class = ''

    if request.method == 'GET':
        if user == qset.owner:
            set_writers = Writer.objects.filter(Q(question_set_writer=qset) | Q(question_set_editor=qset)).distinct().order_by('user__last_name', 'user__first_name', 'user__username')
            available_writers = [writer for writer in Writer.objects.all().order_by('user__last_name', 'user__first_name', 'user__username') #exclude(is_active=False)
                                 if writer not in set_writers and
                                    writer is not qset.owner and writer.id != 1
                                    and writer.user.is_active]
        else:
            available_writers = []
            return render_to_response('failure.html',
                                     {'message': 'You are not authorized to make changes to this tournament!',
                                      'message_class': 'alert-box alert'},
                                      context_instance=RequestContext(request))

        return render_to_response('add_writer.html',
                                 {'qset': qset,
                                  'available_writers': available_writers,
                                  'message': message,
                                  'user': user},
                                  context_instance=RequestContext(request))


    elif request.method == 'POST':
        if user == qset.owner:
            writers_to_add = request.POST.getlist('writers_to_add')
            # do some basic validation here
            if all([x.isdigit() for x in writers_to_add]):
                for writer_id in writers_to_add:
                    writer = Writer.objects.get(id=writer_id)
                    qset.writer.add(writer)
                qset.save()
                cache.clear()
                set_writers = Writer.objects.filter(Q(question_set_writer=qset) | Q(question_set_editor=qset)).distinct().order_by('user__last_name', 'user__first_name', 'user__username')
                available_writers = [writer for writer in Writer.objects.all().order_by('user__last_name', 'user__first_name', 'user__username') #exclude(is_active=False)
                                     if writer not in set_writers and
                                        writer is not qset.owner and writer.id != 1
                                        and writer.user.is_active]
            else:
                message = 'Invalid data entered!'
                available_writers = []
        else:
            available_writers = []
            return render_to_response('failure.html',
                                     {'message': 'You are not authorized to make changes to this tournament!',
                                      'message_class': 'alert-box alert'},
                                      context_instance=RequestContext(request))

        return render_to_response('add_writer.html',
                                 {'qset': qset,
                                  'available_writers': available_writers,
                                  'message': message,
                                  'message_class': message_class,
                                  'user': user},
                                  context_instance=RequestContext(request))


@login_required
def edit_packet(request, packet_id):
    user = request.user.writer
    packet = Packet.objects.get(id=packet_id)
    qset = packet.question_set
    message = ''
    message_class = ''
    read_only = True
    tossup_status = {}
    bonus_status = {}

    if request.method == 'GET':
        if user == qset.owner or user in qset.editor.all() or user in qset.writer.all():
            tossups = packet.tossup_set.order_by('question_number').all()
            bonuses = packet.bonus_set.order_by('question_number').all()
            if user not in qset.writer.all():
                read_only = False

            dist = qset.distribution
            dist_entries = dist.distributionentry_set.all()

            for dist_entry in dist_entries:
                tossups_required = dist_entry.min_tossups
                bonuses_required = dist_entry.min_bonuses
                tu_in_cat = Tossup.objects.filter(packet=packet, category=dist_entry).count()
                bs_in_cat = Bonus.objects.filter(packet=packet, category=dist_entry).count()
                tossup_status[str(dist_entry)] = {'tu_req': tossups_required,
                                                  'tu_in_cat': tu_in_cat}
                bonus_status[str(dist_entry)] = {'bs_req': bonuses_required,
                                                  'bs_in_cat': bs_in_cat}


        else:
            message = 'You are not authorized to view or edit this packet!'
            message_class = 'alert-box alert'
            tossups = None
            bonuses = None

    return render_to_response('edit_packet.html',
        {'qset': qset,
         'packet': packet,
         'message': message,
         'message_class': message_class,
         'tossups': tossups,
         'bonuses': bonuses,
         'tossup_status': tossup_status,
         'bonus_status': bonus_status,
         'read_only': read_only,
         'user': user},
        context_instance=RequestContext(request))

@login_required
def add_tossups(request, qset_id, packet_id=None):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    message = ''
    message_class = ''
    tossup = None
    read_only = True
    question_type_id = []
    tossup_form = []

    if (QuestionType.objects.exists()):
        question_type_id = QuestionType.objects.get(question_type=ACF_STYLE_TOSSUP)

    if request.method == 'GET':
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            if user in qset.writer.all() and user not in qset.editor.all() and user != qset.owner:
                tossup_form = TossupForm(qset_id=qset.id, packet_id=packet_id, role='writer', writer=user.user.username, initial={'question_type': question_type_id})
            else:
                tossup_form = TossupForm(qset_id=qset.id, packet_id=packet_id, writer=user.user.username, initial={'question_type': question_type_id})
            read_only = False
        else:
            tossup_form = []
            message = 'You are not authorized to add questions to this tournament!'
            message_class = 'alert-box warning'
            read_only = True

        return render_to_response('add_tossups.html',
            {'form': tossup_form,
             'message': message,
             'message_class': message_class,
             'read_only': read_only,
             'user': user,
             'qset': qset},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            read_only = False

            # The user may have set the packet ID through the POST body, so check for it there
            if packet_id == None and 'packet' in request.POST and request.POST['packet'] != '':
                packet_id = int(request.POST['packet'])
            tossup_form = TossupForm(request.POST, qset_id=qset.id, packet_id=packet_id, writer=user.user.username)

            if tossup_form.is_valid():
                tossup = tossup_form.save(commit=False)
                if (tossup.author is None):
                    tossup.author = user
                tossup.question_set = qset
                tossup.tossup_text = strip_markup(tossup.tossup_text)
                tossup.tossup_answer = strip_markup(tossup.tossup_answer)
                tossup.locked = False

                try:
                    tossup.is_valid()

                    if packet_id is None or packet_id == '':
                        # If the tossup doesn't have a packet, set its number to be the magic number
                        # of 999, meaning that it's unassigned.  Can't assign -1 because this is outside
                        # of the legal range of tossup numbers and it ends up getting set to 1 for some
                        # reason, except in the case where there are no packets in the system in which
                        # case there's an error adding the question
                        tossup.question_number = 999
                    else:
                        tossup.packet_id = packet_id
                        tossup.question_number = Tossup.objects.filter(packet_id=packet_id).count()

                    tossup.save_question(edit_type=QUESTION_CREATE, changer=user)
                    cache.clear()
                    message = 'Your tossup has been added to the set.'
                    message_class = 'alert-box info radius'

                    # In the success case, don't return the whole tossup object so as to clear the fields
                    return render_to_response('add_tossups.html',
                             {'form': TossupForm(qset_id=qset.id, packet_id=packet_id, initial={'question_type': question_type_id}, writer=user.user.username),
                             'message': message,
                             'message_class': message_class,
                             'tossup' : None,
                             'tossup_id': tossup.id,
                             'read_only': read_only,
                             'user': user,
                             'qset': qset},
                             context_instance=RequestContext(request))

                except InvalidTossup as ex:
                    message = str(ex)
                    message_class = 'alert-box warning'

            else:
                message = 'Problem adding a tossup.  Make sure that all required fields are filled out!'
                message_class = 'alert-box warning'

        else:
            tossup = None
            message = 'You are not authorized to add questions to this tournament!'
            message_class = 'alert-box warning'
            tossup_form = []
            read_only = True
            
        if (tossup_form is None):
            tossup_form = TossupForm(qset_id=qset.id, packet_id=packet_id, initial={'question_type': question_type_id})

        # In the error case, return the whole tossup object so you can edit it
        return render_to_response('add_tossups.html',
                 {'form': tossup_form,
                 'message': message,
                 'message_class': message_class,
                 'tossup' : tossup,
                 'tossup_id': None,
                 'read_only': read_only,
                 'user': user,
                 'qset': qset},
                 context_instance=RequestContext(request))

    else:
        return render_to_response('failure.html',
            {'message': 'The request cannot be completed as specified',
             'message_class': 'alert-box alert'},
            context_instance=RequestContext(request))

@login_required
def add_bonuses(request, qset_id, bonus_type, packet_id=None):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    message = ''
    message_class = ''
    read_only = True
    role = get_role_no_owner(user, qset)
    question_type_id = []
    bonus_form = []

    if (QuestionType.objects.exists()):
        if (bonus_type == VHSL_BONUS):
            question_type_id = QuestionType.objects.get(question_type=VHSL_BONUS)
        elif (bonus_type == ACF_STYLE_BONUS):
            question_type_id = QuestionType.objects.get(question_type=ACF_STYLE_BONUS)
        else:
            return render_to_response('failure.html',
                {'message': 'The request cannot be completed as specified.  Bonus type is invalid.',
                 'message_class': 'alert-box alert'},
                context_instance=RequestContext(request))

    if request.method == 'GET':
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            form = BonusForm(qset_id=qset.id, packet_id=packet_id, role=role, initial={'question_type': question_type_id}, writer=user.user.username, question_type=bonus_type)
            read_only = False
        else:
            form = None
            message = 'You are not authorized to add questions to this tournament!'
            message_class = 'alert-box warning'
            read_only = True

        return render_to_response('add_bonuses.html',
            {'form': form,
             'message': message,
             'message_class': message_class,
             'read_only': read_only,
             'question_type': bonus_type,
             'user': user,
             'qset': qset},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        bonus = None
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            bonus_form = BonusForm(request.POST, qset_id=qset.id, packet_id=packet_id, initial={'question_type': question_type_id}, writer=user.user.username, question_type=bonus_type)
            read_only = False

            if bonus_form.is_valid():
                bonus = bonus_form.save(commit=False)
                if (bonus.author is None):
                    bonus.author = user

                bonus.question_set = qset
                bonus.leadin = strip_markup(bonus.leadin)
                bonus.part1_text = strip_markup(bonus.part1_text)
                bonus.part1_answer = strip_markup(bonus.part1_answer)
                bonus.part2_text = strip_markup(bonus.part2_text)
                bonus.part2_answer = strip_markup(bonus.part2_answer)
                bonus.part3_text = strip_markup(bonus.part3_text)
                bonus.part3_answer = strip_markup(bonus.part3_answer)
                bonus.locked = False

                if packet_id is None or packet_id == '':
                    # If the bonus doesn't have a packet, set its number to be the magic number
                    # of 999, meaning that it's unassigned.  Can't assign -1 because this is outside
                    # of the legal range of bonus numbers and it ends up getting set to 1 for some
                    # reason, except in the case where there are no packets in the system in which
                    # case there's an error adding the question
                    bonus.question_number = 999
                else:
                    bonus.packet_id = packet_id
                    bonus.question_number = Bonus.objects.filter(packet_id=packet_id).count()

                try:
                    bonus.is_valid()
                    bonus.save_question(edit_type=QUESTION_CREATE, changer=user)
                    cache.clear()
                    message = 'Your bonus has been added to the set.'
                    message_class = 'alert-box success'

                    # On success case, don't return the full bonus so that field gets cleared
                    return render_to_response('add_bonuses.html',
                             {'form': BonusForm(qset_id=qset.id, packet_id=packet_id, initial={'question_type': question_type_id}, writer=user.user.username, question_type=bonus_type),
                             'message': message,
                             'message_class': message_class,
                             'bonus': None,
                             'bonus_id': bonus.id,
                             'read_only': read_only,
                             'question_type': bonus_type,
                             'user': user,
                             'qset': qset},
                             context_instance=RequestContext(request))

                except InvalidBonus as ex:
                    message = str(ex)
                    message_class = 'alert-box alert'

            else:
                message = 'There was an error with the form: ' + str(bonus_form.errors)
                message_class = 'alert-box alert'

            read_only = False
        else:
            message = 'You are not authorized to add questions to this tournament!'
            message_class = 'alert-box alert'
            bonus_form = []
            bonus = None
            read_only = True

        if (bonus_form is None):
            bonus_form = BonusForm(qset_id=qset.id, packet_id=packet_id, initial={'question_type': question_type_id}, writer=user.user.username)

        return render_to_response('add_bonuses.html',
                 {'form': bonus_form,
                 'message': message,
                 'message_class': message_class,
                 'bonus': bonus,
                 'bonus_id': None,
                 'read_only': read_only,
                 'question_type': bonus_type,
                 'user': user,
                 'qset': qset},
                 context_instance=RequestContext(request))

    else:
        return render_to_response('failure.html',
            {'message': 'The request cannot be completed as specified',
             'message_class': 'alert-box alert'},
            context_instance=RequestContext(request))

@login_required
def edit_tossup(request, tossup_id):
    user = request.user.writer
    tossup = Tossup.objects.get(id=tossup_id)
    tossup_length = tossup.character_count()
    qset = tossup.question_set
    packet = tossup.packet
    message = ''
    message_class = ''
    read_only = True
    role = get_role_no_owner(user, qset)

    if request.method == 'GET':
        if user == tossup.author or user == qset.owner or user in qset.editor.all():
            form = TossupForm(instance=tossup, qset_id=qset.id, role=role)
            if user == tossup.author and not user == qset.owner and not user in qset.editor.all() and tossup.locked:
                read_only = True
                message = 'This tossup has been locked by an editor. It cannot be changed except by another editor.'
                message_class = 'alert-box warning'
            else:
                read_only = False

        elif user in qset.writer.all():
            read_only = True
            form = None
        else:
            read_only = True
            tossup = None
            form = None
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert-box alert'

        return render_to_response('edit_tossup.html',
            {'tossup': tossup,
             'tossup_length': tossup_length,
             'form': form,
             'qset': qset,
             'packet': packet,
             'message': message,
             'message_class': message_class,
             'read_only': read_only,
             'role': role,
             'user': user},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        print "start post for edit tossup"
        if user == tossup.author or user == qset.owner or user in qset.editor.all():
            form = TossupForm(request.POST, qset_id=qset.id, role=role)
            can_change = True
            if tossup.locked and not (user == qset.owner or user in qset.editor.all()):
                can_change = False

            if form.is_valid() and can_change:
                read_only = False

                is_tossup_already_edited = tossup.edited
                is_tossup_already_proofread = tossup.proofread
                is_tossup_already_read_carefully = tossup.read_carefully

                tossup.tossup_text = strip_markup(form.cleaned_data['tossup_text'])
                tossup.tossup_answer = strip_markup(form.cleaned_data['tossup_answer'])
                tossup.category = form.cleaned_data['category']
                tossup.packet = form.cleaned_data['packet']
                tossup.locked = form.cleaned_data['locked']
                tossup.edited = form.cleaned_data['edited']
                tossup.proofread = form.cleaned_data['proofread']
                tossup.read_carefully = form.cleaned_data['read_carefully']
                tossup.question_type = form.cleaned_data['question_type']
                tossup.author = form.cleaned_data['author']
                print "trying to save tossup"

                try:
                    tossup.is_valid()
                    change_type = QUESTION_CHANGE
                    if (not is_tossup_already_edited and tossup.edited == True):
                        change_type = QUESTION_EDIT

                    if (not is_tossup_already_proofread and tossup.proofread == True):
                        change_type = QUESTION_PROOFREAD

                    if (not is_tossup_already_read_carefully and tossup.read_carefully == True):
                        change_type = QUESTION_READ_CAREFULLY

                    tossup.save_question(edit_type=change_type, changer=user)
                    tossup_length = tossup.character_count()
                    cache.clear()
                    print "Tossup saved"
                    message = 'Your changes have been saved!'
                    message_class = 'alert-box success'                    

                except InvalidTossup as ex:
                    message = str(ex)
                    message_class = 'alert-box warning'

            elif form.is_valid() and not can_change:
                message = 'This tossup is locked and can only be changed by an editor!'
                message_class = 'alert-box warning'
                read_only = True
            else:
                message = 'There was an error with the form: ' + str(form.errors)
                message_class = 'alert-box warning'


        elif user in qset.writer.all():
            read_only = True
            form = None
            message = 'You are only authorized to view, not to edit, this question!'
            message_class = 'alert-box warning'
        else:
            read_only = True
            tossup = None
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert-box alert'

        return render_to_response('edit_tossup.html',
            {'tossup': tossup,
             'tossup_length': tossup_length,
             'form': form,
             'role': role,
             'qset': qset,
             'packet': packet,
             'message': message,
             'message_class': message_class,
             'read_only': read_only,
             'user': user},
            context_instance=RequestContext(request))

@login_required
def edit_bonus(request, bonus_id):
    user = request.user.writer
    bonus = Bonus.objects.get(id=bonus_id)
    char_count = bonus.character_count()
    qset = bonus.question_set
    packet = bonus.packet
    message = ''
    message_class = ''
    read_only = True
    role = get_role_no_owner(user, qset)

    question_type = ACF_STYLE_BONUS
    if (bonus.question_type is not None):
        question_type = bonus.question_type.question_type
        
    if request.method == 'GET':
        if user == bonus.author or user == qset.owner or user in qset.editor.all():
            form = BonusForm(instance=bonus, qset_id=qset.id, role=role, question_type=question_type)
            if user == bonus.author and not user == qset.owner and not user in qset.editor.all() and bonus.locked:
                read_only = True
                message = 'This bonus has been locked by an editor. It cannot be changed except by another editor.'
                message_class = 'alert-box warning'
            else:
                read_only = False

        elif user in qset.writer.all():
            read_only = True
            form = None
        else:
            read_only = True
            bonus = None
            form = None
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert-box alert'

        return render_to_response('edit_bonus.html',
            {'bonus': bonus,
             'char_count': char_count,
             'question_type': question_type,
             'form': form,
             'qset': qset,
             'packet': packet,
             'message': message,
             'message_class': message_class,
             'read_only': read_only,
             'role': role,
             'user': user},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        if user == bonus.author or user == qset.owner or user in qset.editor.all():
            form = BonusForm(request.POST, qset_id=qset.id, role=role, question_type=question_type)
            
            can_change = True
            if bonus.locked and not (user == qset.owner or user in qset.editor.all()):
                can_change = False

            if form.is_valid() and can_change:
                is_bonus_already_edited = bonus.edited
                is_bonus_already_proofread = bonus.proofread
                is_bonus_already_read_carefully = bonus.read_carefully

                bonus.leadin = strip_markup(form.cleaned_data['leadin'])
                bonus.part1_text = strip_markup(form.cleaned_data['part1_text'])
                bonus.part1_answer = strip_markup(form.cleaned_data['part1_answer'])
                bonus.part2_text = strip_markup(form.cleaned_data['part2_text'])
                bonus.part2_answer = strip_markup(form.cleaned_data['part2_answer'])
                bonus.part3_text = strip_markup(form.cleaned_data['part3_text'])
                bonus.part3_answer = strip_markup(form.cleaned_data['part3_answer'])
                bonus.category = form.cleaned_data['category']
                bonus.packet = form.cleaned_data['packet']
                bonus.locked = form.cleaned_data['locked']
                bonus.edited = form.cleaned_data['edited']
                bonus.proofread = form.cleaned_data['proofread']
                bonus.read_carefully = form.cleaned_data['read_carefully']
                bonus.question_type = form.cleaned_data['question_type']
                bonus.author = form.cleaned_data['author']

                try:
                    bonus.is_valid()
                    change_type = QUESTION_CHANGE
                    if (not is_bonus_already_edited and bonus.edited):
                        change_type = QUESTION_EDIT

                    if (not is_bonus_already_proofread and bonus.proofread):
                        change_type = QUESTION_PROOFREAD
                        
                    if (not is_bonus_already_read_carefully and bonus.read_carefully):
                        change_type = QUESTION_READ_CAREFULLY

                    bonus.save_question(edit_type=change_type, changer=user)
                    char_count = bonus.character_count()
                    cache.clear()

                    message = 'Your changes have been saved!'
                    message_class = 'alert-box success'
                    read_only = False
                except InvalidBonus as ex:
                    message = str(ex)
                    message_class = 'alert-box warning'
                    read_only = False

            elif form.is_valid() and not can_change:
                message = 'This bonus is locked and can only be changed by an editor!'
                message_class = 'alert-box warning'
                read_only = True
            else:
                message = 'There was an error with the form: ' + str(form.errors)
                message_class = 'alert-box warning'

        elif user in qset.writer.all():
            form = None
            read_only = True
            message = 'You are only authorized to view, not to edit, this question!'
            message_class = 'alert-box warning'
        else:
            form = None
            bonus = None
            read_only = True
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert-box alert'

        return render_to_response('edit_bonus.html',
            {'bonus': bonus,
             'char_count': char_count,
             'question_type': question_type,
             'form': form,
             'qset': qset,
             'packet': packet,
             'message': message,
             'message_class': message_class,
             'read_only': read_only,
             'role': role,
             'user': user},
            context_instance=RequestContext(request))

@login_required
def delete_tossup(request):
    user = request.user.writer
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'POST':
        tossup_id = int(request.POST['tossup_id'])
        tossup = Tossup.objects.get(id=tossup_id)
        qset = tossup.question_set
        if user == tossup.author or user == qset.owner or user in qset.editor.all():
            tossup.delete()
            message = 'Tossup deleted'
            message_class = 'alert-box success'
            read_only = False
        else:
            message = 'You are not authorized to delete questions from this set!'
            message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def delete_bonus(request):
    user = request.user.writer
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'POST':
        bonus_id = int(request.POST['bonus_id'])
        bonus = Bonus.objects.get(id=bonus_id)
        qset = bonus.question_set
        if user == bonus.author or user == qset.owner or user in qset.editor.all():
            bonus.delete()
            cache.clear()
            message = 'Bonus deleted'
            message_class = 'alert-box success'
            read_only = False
        else:
            message = 'You are not authorized to delete questions from this set!'
            message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def delete_writer(request):
    user = request.user.writer
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'POST':
        qset_id = request.POST['qset_id']
        qset = QuestionSet.objects.get(id=qset_id)
        writer_id = request.POST['writer_id']
        writer = qset.writer.get(id=writer_id)
        role = get_role_no_owner(user, qset)
        if role == "editor":
            qset.writer.remove(writer)
            cache.clear()
            message = 'Writer removed'
            message_class = 'alert-box success'
        else:
            message = 'You are not authorized to remove writers from this set!'
            message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def delete_editor(request):
    user = request.user.writer
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'POST':
        qset_id = request.POST['qset_id']
        qset = QuestionSet.objects.get(id=qset_id)
        editor_id = request.POST['editor_id']
        editor = qset.editor.get(id=editor_id)
        role = get_role_no_owner(user, qset)
        if role == "editor":
            qset.editor.remove(editor)
            cache.clear()
            message = 'Editor removed'
            message_class = 'alert-box success'
        else:
            message = 'You are not authorized to remove editors from this set!'
            message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def delete_set(request):
    user = request.user.writer
    message = ''
    message_class = ''
    read_only = True

    print("In editor removed")
    if request.method == 'POST':
        qset_id = request.POST['qset_id']
        qset = QuestionSet.objects.get(id=qset_id)
        role = get_role_no_owner(user, qset)
        if role == "editor":
            qset.delete()
            cache.clear()
            message = 'Set deleted'
            message_class = 'alert-box success'
        else:
            message = 'You are not authorized to delete this set!'
            message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def delete_comment(request):
    user = request.user.writer
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'POST':
        qset_id = request.POST['qset_id']
        qset = QuestionSet.objects.get(id=qset_id)
        qset_editors = qset.editor.all()
        comment_id = request.POST['comment_id']
        comment = Comment.objects.get(id=comment_id)

        if (comment is None):
            message = 'Error retrieving comment.'
            message_class = 'alert-box warning'
        else:
            if user in qset_editors:
                comment.is_removed = True
                comment.save()
                cache.clear()
                message = 'Comment removed'
                message_class = 'alert-box success'
            else:
                message = 'You are not authorized to remove comments from this set!'
                message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def delete_all_comments(request):
    user = request.user.writer
    message = ''
    message_class = ''
    read_only = True

    tossup_content_type_id = ContentType.objects.get_for_model(Tossup).id
    bonus_content_type_id = ContentType.objects.get_for_model(Bonus).id

    if request.method == 'POST':
        qset_id = request.POST['qset_id']
        qset = QuestionSet.objects.get(id=qset_id)
        qset_editors = qset.editor.all()
        question_type = request.POST['question_type']
        question_id = request.POST['question_id']

        if (question_type == 'tossup'):
            comment_list = Comment.objects.filter(content_type_id=tossup_content_type_id).filter(object_pk=question_id).order_by('submit_date')
        else:
            comment_list = Comment.objects.filter(content_type_id=bonus_content_type_id).filter(object_pk=question_id).order_by('submit_date')

        if (comment_list is None):
            message = 'Error retrieving comments.'
            message_class = 'alert-box warning'
        else:
            if user in qset_editors:
                for comment in comment_list:
                    comment.is_removed = True
                    comment.save()
                    cache.clear()

                message = 'Comments removed'
                message_class = 'alert-box success'
            else:
                message = 'You are not authorized to remove comments from this set!'
                message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def add_packets(request, qset_id):

    qset = QuestionSet.objects.get(id=qset_id)
    user = request.user.writer
    message = ''
    message_class = ''

    if user == qset.owner:
        if request.method == 'GET':
            form = NewPacketsForm()
        elif request.method == 'POST':
            form = NewPacketsForm(data=request.POST)
            if form.is_valid():
                packet_name = form.cleaned_data['packet_name']
                name_base = form.cleaned_data['name_base']
                num_packets = form.cleaned_data['num_packets']
                if packet_name and len(packet_name.strip()) > 0 and (name_base is None or num_packets is None):
                    if Packet.objects.filter(question_set=qset, packet_name=packet_name).exists():
                        message = 'The packet name "{0}" arleady exists.'.format(packet_name)
                        message_class = 'alert-box warning'
                    else:
                        new_packet = Packet()
                        new_packet.packet_name = packet_name
                        new_packet.created_by = user
                        new_packet.question_set = qset
                        new_packet.save()
                        cache.clear()
                        message = 'Your packet named {0} has been created.'.format(packet_name)
                        message_class = 'alert-box success'

                elif name_base and len(name_base.strip()) > 0 and num_packets is not None:
                    create_all_failed = False
                    for i in range(1, num_packets + 1):
                        new_packet = Packet()
                        packet_name = '{0!s} {1:02}'.format(name_base, i)
                        if Packet.objects.filter(question_set=qset, packet_name=packet_name).exists():
                            message = 'The packet name "{0}" arleady exists.'.format(packet_name)
                            message_class = 'alert-box warning'
                            create_all_failed = True
                            break
                        new_packet.packet_name = packet_name
                        new_packet.created_by = user
                        new_packet.question_set = qset
                        new_packet.save()
                        cache.clear()
                    if not create_all_failed:
                        message = 'Your {0} packet(s) with the base name {1} have been created.'.format(num_packets, name_base)
                        message_class = 'alert-box success'
                else:
                    message = 'You must enter either the name for an individual packet or a base name and the number of packets to create!'
                    message_class = 'alert-box warning'

            else:
                message = 'Invalid information entered into form!'
                message_class = 'alert-box alert'
        else:
            message = 'Invalid method!'
            message_class = 'alert-box alert'
            form = None

    else:
        message = 'You are not authorized to add packets to this set!'
        message_class = 'alert-box alert'
        form = None

    return render_to_response('add_packets.html',
                             {'message': message,
                              'message_class': message_class,
                              'form': form,
                              'qset': qset,
                              'user': user},
                              context_instance=RequestContext(request))

@login_required
def delete_packet(request):
    user = request.user.writer
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'POST':
        packet_id = int(request.POST['packet_id'])
        packet = Packet.objects.get(id=packet_id)
        qset = packet.question_set
        if user == qset.owner:
            packet.delete()
            cache.clear()
            message = 'Packet deleted'
            message_class = 'alert-box success'
            read_only = False
        else:
            message = 'You are not authorized to delete packets from this set!'
            message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def get_unassigned_tossups(request):
    user = request.user.writer
    qset_id = request.GET['qset_id']
    message = ''
    message_class = ''
    data = []

    try:
        qset = QuestionSet.objects.get(id=qset_id)

        if request.method == 'GET':
            if user == qset.owner:
                available_tossups = Tossup.objects.filter(question_set=qset, packet=None)
                for tu in available_tossups:
                    data.append(tu.to_json())
            else:
                available_tossups = []
                message = 'Only the set owner has the power to add questions to it!'
                message_class = 'alert-box alert'

        else:
            message = 'Invalid request!'
            message_class = 'alert-box alert'
    except Exception as ex:
        print ex
        message = 'Unable to retrieve question set; qset_id either missing or incorrect!'
        message_class = 'alert-box alert'

    return HttpResponse(json.dumps(data))

@login_required
def get_unassigned_bonuses(request):
    user = request.user.writer
    qset_id = request.GET['qset_id']
    message = ''
    message_class = ''
    data = []

    try:
        qset = QuestionSet.objects.get(id=qset_id)

        if request.method == 'GET':
            if user == qset.owner:
                available_bonuses= Bonus.objects.filter(question_set=qset, packet=None)
                for bs in available_bonuses:
                    data.append(bs.to_json())
            else:
                available_tossups = []
                message = 'Only the set owner has the power to add questions to it!'
                message_class = 'alert-box alert'

        else:
            message = 'Invalid request!'
            message_class = 'alert-box alert'
    except Exception as ex:
        print ex
        message = 'Unable to retrieve question set; qset_id either missing or incorrect!'
        message_class = 'alert-box alert'

    return HttpResponse(json.dumps(data))

@login_required
def assign_tossups_to_packet(request):

    user = request.user.writer
    packet_id = int(request.POST['packet_id'])
    tossup_ids = request.POST.getlist('tossup_ids[]')
    packet = Packet.objects.get(id=packet_id)
    qset = packet.question_set
    message = ''
    message_class = ''


    if request.method == 'POST':
        if user == qset.owner:
            for tu_id in tossup_ids:
                tossup = Tossup.objects.get(id=tu_id)
                tossup.packet = packet
                # Potential race condition?
                tossup.question_number = Tossup.objects.filter(packet_id=packet_id).count()
                message = 'Your tossups have been added to the set!'
                message_class = 'alert-box success'
                tossup.save()
                cache.clear()
        else:
            message = 'Only the set owner is authorized to add questions to the set!'
            message_class = 'alert-box warning'

    else:
        message = 'Invalid request!'
        message_class = 'alert-box alert'

    return HttpResponse(json.dumps({'message': message,
                                    'message_class': message_class}))

@login_required
def assign_bonuses_to_packet(request):

    user = request.user.writer
    packet_id = int(request.POST['packet_id'])
    bonus_ids = request.POST.getlist('bonus_ids[]')
    packet = Packet.objects.get(id=packet_id)
    qset = packet.question_set
    message = ''
    message_class = ''

    if request.method == 'POST':
        if user == qset.owner:
            for bs_id in bonus_ids:
                bonus = Bonus.objects.get(id=bs_id)
                bonus.packet = packet
                print packet, bonus
                message = 'Your bonuses have been added to the set!'
                message_class = 'alert-box success'
                bonus.save()
                cache.clear()
        else:
            message = 'Only the set owner is authorized to add questions to the set!'
            message_class = 'alert-box warning'

    else:
        message = 'Invalid request!'
        message_class = 'alert-box alert'

    return HttpResponse(json.dumps({'message': message,
                                    'message_class': message_class}))

@login_required
def change_question_order(request):

    user = request.user.writer
    packet_id = int(request.POST['packet_id'])
    num_questions = int(request.POST['num_questions'])
    question_type = request.POST['question_type']
    packet = Packet.objects.get(id=packet_id)
    qset = packet.question_set

    if request.method == 'POST':
        if user == qset.owner:
            try:
                for i in range(num_questions):
                    id_key = 'order_data[{0}][id]'.format(i)
                    order_key = 'order_data[{0}][order]'.format(i)
                    id = int(request.POST[id_key])
                    order = int(request.POST[order_key])
                    if question_type == 'tossup':
                        question = Tossup.objects.get(id=id)
                    elif question_type == 'bonus':
                        question = Bonus.objects.get(id=id)
                    question.question_number = order
                    question.save()
                    cache.clear()
                message = ''
                message_class = ''

            except Exception as ex:
                print ex
                message = 'Something went terribly wrong!'
                message_class = 'alert-box alert'

        else:
            message = 'Only the owner of the set is allowed to change the order of questions!'
            message_class = 'alert-box warning'
    else:
        message = 'Invalid request!'
        message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

# @login_required
# def change_tossup_order(request):
#     # packet_id, old_index, new_index
#     packet_id = int(request.POST['packet_id'])
#     user = request.user.writer
#     packet = Packet.objects.get(id=packet_id)
#     qset = packet.question_set
#
#     old_index = int(request.POST['old_index'])
#     new_index = int(request.POST['new_index'])
#
#     if request.method == 'POST':
#         if user == qset.owner:
#             change_question_order(packet, int(old_index), int(new_index), Tossup)
#             message = ''
#             message_class = ''
#         else:
#             message = 'Only the set owner is authorized to change question order'
#             message_class = 'alert-box warning'
#     else:
#         message = 'Invalid request!'
#         message_class = 'alert-box alert'
#
#     return HttpResponse(json.dumps({'message': message,
#                                     'message_class': message_class}))


# @login_required
# def change_bonus_order(request):
#     user = request.user.writer
#     packet = Packet.objects.get(id=packet_id)
#     qset = packet.question_set
#
#     if request.method == 'POST':
#         if user == qset.owner:
#             change_question_order(packet, int(old_index), int(new_index), Bonus)
#             message = ''
#             message_class = ''
#         else:
#             message = 'Only the set owner is authorized to change question order'
#             message_class = 'alert-box warning'
#     else:
#         message = 'Invalid request!'
#         message_class = 'alert-box alert'
#     return HttpResponse(json.dumps({'message': message,
#                                     'message_class': message_class}))
#
# # Not a URL action, just a helper method. old_index and new_index should be integers
# def change_question_order(packet, old_index, new_index, model_class):
#     if old_index != new_index and old_index >= 0 and new_index >= 0:
#         # If oldIndex < newIndex, decrease question_number for questions [oldIndex + 1, newIndex]
#         # Otherwise, increase question_number for questions [newIndex, oldIndex - 1]
#         lowerIndex = old_index + 1 if old_index < new_index else new_index
#         higherIndex = old_index - 1 if old_index > new_index else new_index
#
#         selected_question = model_class.objects.get(packet=packet, question_number=old_index)
#         selected_id = selected_question.id
#         reordered_questions = model_class.objects.filter(packet=packet, question_number__range=(lowerIndex, higherIndex))
#         # This prevents a race condition where selected_question's question_number is set to something in the range
#         # before this QuerySet is evaluated.
#         reordered_questions = reordered_questions.exclude(id=selected_id)
#         selected_question.question_number = new_index
#         selected_question.save()
#
#         direction = -1 if old_index < new_index else 1
#         for question in reordered_questions:
#             question.question_number += direction
#             question.save()

@login_required
def distributions (request):

    data = []
    all_dists = Distribution.objects.all()

    return render_to_response('distributions.html',
                             {'dists': all_dists,
                              'user': request.user.writer},
                              context_instance=RequestContext(request))

@login_required
def edit_distribution(request, dist_id=None):

    data = []
    message = ''
    message_class = ''

    if request.user.is_authenticated():
        DistributionEntryFormset = formset_factory(DistributionEntryForm, can_delete=True)
        if request.method == 'POST':
            # no dist_id supplied means new dist
            if dist_id is None:
                formset = DistributionEntryFormset(data=request.POST, prefix='distentry')
                dist_form = DistributionForm(data=request.POST)
                if dist_form.is_valid() and formset.is_valid():
                    new_dist = Distribution()
                    new_dist.name = dist_form.cleaned_data['name']
                    new_dist.save()

                    for form in formset:
                        if form.cleaned_data != {}:
                            new_entry = DistributionEntry()
                            new_entry.category = form.cleaned_data['category']
                            new_entry.subcategory = form.cleaned_data['subcategory']
                            new_entry.min_bonuses = form.cleaned_data['min_bonuses']
                            new_entry.min_tossups = form.cleaned_data['min_tossups']
                            new_entry.max_bonuses = form.cleaned_data['max_bonuses']
                            new_entry.max_tossups = form.cleaned_data['max_tossups']
                            if new_entry.min_bonuses > new_entry.max_bonuses:
                                new_entry.min_bonuses = new_entry.max_bonuses
                                #TODO: display the message
                                message = 'Minimum bonuses for ' + new_entry.category + ' - ' + new_entry.subcategory +\
                                          ' was higher than maximum bonuses and has been set to maximum bonuses.'
                                message_class = 'alert-box warning'
                            if new_entry.min_tossups > new_entry.max_tossups:
                                new_entry.min_tossups = new_entry.max_tossups
                                #TODO: display the message
                                message = 'Minimum tossups for ' + new_entry.category + ' - ' + new_entry.subcategory +\
                                          ' was higher than maximum tossups and has been set to maximum tossups.'
                                message_class = 'alert-box warning'

                            new_entry.distribution = new_dist
                            new_entry.save()

                    return HttpResponseRedirect('/edit_distribution/' + str(new_dist.id))

            else:
                dist_form = DistributionForm(data=request.POST)
                #print dist_form.is_valid()
                #print formset.is_valid()
                #print formset.errors
                if 'add_row' in request.POST:
                    distentry_post = request.POST.copy()
                    #TODO: grab a value from an input
                    num_rows = 1
                    distentry_post['distentry-TOTAL_FORMS'] = int(distentry_post['distentry-TOTAL_FORMS']) + num_rows
                    formset = DistributionEntryFormset(data=distentry_post, prefix='distentry')
                else:
                    formset = DistributionEntryFormset(data=request.POST, prefix='distentry')
                    if dist_form.is_valid() and formset.is_valid():
                        dist = Distribution.objects.get(id=dist_id)
                        dist.name = dist_form.cleaned_data['name']
                        dist.save()

                        qsets = dist.questionset_set.all()
                        for form in formset:
                            if form.cleaned_data != {}:
                                if form.cleaned_data['entry_id'] is not None:
                                    entry_id = int(form.cleaned_data['entry_id'])
                                    entry = DistributionEntry.objects.get(id=entry_id)
                                    if form.cleaned_data['DELETE']:
                                        entry.delete()
                                        entry = None
                                    else:
                                        entry.category = form.cleaned_data['category']
                                        entry.subcategory = form.cleaned_data['subcategory']
                                        entry.min_bonuses = form.cleaned_data['min_bonuses']
                                        entry.min_tossups = form.cleaned_data['min_tossups']
                                        entry.max_bonuses = form.cleaned_data['max_bonuses']
                                        entry.max_tossups = form.cleaned_data['max_tossups']
                                        if entry.min_bonuses > entry.max_bonuses:
                                            entry.min_bonuses = entry.max_bonuses
                                            message = 'Minimum bonuses for ' + entry.category + ' - ' + entry.subcategory +\
                                                      ' was higher than maximum bonuses and has been set to maximum bonuses.'
                                            message_class = 'alert-box warning'
                                        if entry.min_tossups > entry.max_tossups:
                                            entry.min_tossups = entry.max_tossups
                                            message = 'Minimum tossups for ' + entry.category + ' - ' + entry.subcategory +\
                                                      ' was higher than maximum tossups and has been set to maximum tossups.'
                                            message_class = 'alert-box warning'

                                        entry.save()
                                else:
                                    entry = form.save(commit=False)
                                    entry.distribution = dist
                                    entry.save()

                                if entry is not None:
                                    for qset in qsets:
                                        set_wide_entry = qset.setwidedistributionentry_set.filter(dist_entry=entry)
                                        print set_wide_entry
                                        if set_wide_entry.count() == 0:
                                            new_set_wide_entry = SetWideDistributionEntry()
                                            new_set_wide_entry.dist_entry = entry
                                            new_set_wide_entry.question_set = qset
                                            new_set_wide_entry.num_tossups = qset.num_packets * entry.min_tossups
                                            new_set_wide_entry.num_bonuses = qset.num_packets * entry.min_bonuses
                                            new_set_wide_entry.save()

                        entries = dist.distributionentry_set.all()
                        initial_data = []
                        for entry in entries:
                            initial_data.append({'entry_id': entry.id,
                                                 'category': entry.category,
                                                 'subcategory': entry.subcategory,
                                                 'min_tossups': entry.min_tossups,
                                                 'min_bonuses': entry.min_bonuses,
                                                 'max_tossups': entry.max_tossups,
                                                 'max_bonuses': entry.max_bonuses})
                        formset = DistributionEntryFormset(initial=initial_data, prefix='distentry')

                    else:
                        dist = Distribution.objects.get(id=dist_id)
                        dist_form = DistributionForm(instance=dist)
                        formset = DistributionEntryFormset(data=request.POST, prefix='distentry')

            return render_to_response('edit_distribution.html',
                                     {'form': dist_form,
                                      'formset': formset,
                                      'message': message,
                                      'message_class': message_class,
                                      'user': request.user.writer},
                                      context_instance=RequestContext(request))
        else:
            if dist_id is not None:
                dist = Distribution.objects.get(id=dist_id)
                entries = dist.distributionentry_set.all()
                initial_data = []
                for entry in entries:
                    initial_data.append({'entry_id': entry.id,
                                         'category': entry.category,
                                         'subcategory': entry.subcategory,
                                         'min_tossups': entry.min_tossups,
                                         'min_bonuses': entry.min_bonuses,
                                         'max_tossups': entry.max_tossups,
                                         'max_bonuses': entry.max_bonuses})
                dist_form = DistributionForm(instance=dist)
                formset = DistributionEntryFormset(initial=initial_data, prefix='distentry')
            else:
                dist_form = DistributionForm()
                formset = DistributionEntryFormset(prefix='distentry')

            return render_to_response('edit_distribution.html',
                                     {'form': dist_form,
                                      'formset': formset,
                                      'message': message,
                                      'message_class': message_class,
                                      'user': request.user.writer},
                                      context_instance=RequestContext(request))

@login_required()
def edit_tiebreak(request, dist_id=None):

    user = request.user.writer
    data = []


    TiebreakDistributionEntryFormset = formset_factory(TieBreakDistributionEntryForm, can_delete=True)
    if request.method == 'POST':
        # no dist_id supplied means new dist
        if dist_id is None:
            formset = TiebreakDistributionEntryFormset(data=request.POST, prefix='tiebreak')
            dist_form = TieBreakDistributionForm(data=request.POST)
            if dist_form.is_valid() and formset.is_valid():
                new_dist = TieBreakDistribution()
                new_dist.name = dist_form.cleaned_data['name']
                new_dist.save()

                for form in formset:
                    if form.cleaned_data != {}:
                        new_entry = DistributionEntry()
                        new_entry.category = form.cleaned_data['category']
                        new_entry.subcategory = form.cleaned_data['subcategory']
                        new_entry.bonuses = form.cleaned_data['num_bonuses']
                        new_entry.tossups = form.cleaned_data['num_tossups']
                        new_entry.distribution = new_dist
                        new_entry.save()

                return HttpResponseRedirect('/edit_tiebreak/' + str(new_dist.id))
        else:
            formset = TiebreakDistributionEntryFormset(data=request.POST, prefix='tiebreak')
            dist_form = TieBreakDistributionForm(data=request.POST)
            print dist_form.is_valid()
            print formset.is_valid()
            print formset.errors
            if dist_form.is_valid() and formset.is_valid():

                dist = TieBreakDistribution.objects.get(id=dist_id)
                dist.name = dist_form.cleaned_data['name']
                qsets = dist.questionset_set.all()
                for form in formset:
                    if form.cleaned_data != {}:
                        if form.cleaned_data['entry_id'] is not None:
                            entry_id = int(form.cleaned_data['entry_id'])
                            entry = DistributionEntry.objects.get(id=entry_id)
                            if form.cleaned_data['DELETE']:
                                entry.delete()
                                entry = None
                            else:
                                entry.category = form.cleaned_data['category']
                                entry.subcategory = form.cleaned_data['subcategory']
                                entry.bonuses = form.cleaned_data['num_bonuses']
                                entry.tossups = form.cleaned_data['num_tossups']
                                entry.save()
                        else:
                            entry = form.save(commit=False)
                            entry.distribution = dist
                            entry.save()

                        if entry is not None:
                            for qset in qsets:
                                set_wide_entry = qset.tiebreakdistributionentry_set.filter(dist_entry=entry)
                                print set_wide_entry
                                if set_wide_entry.count() == 0:
                                    print 'here'
                                    new_set_wide_entry = DistributionEntry()
                                    new_set_wide_entry.dist_entry = entry
                                    new_set_wide_entry.question_set = qset
                                    new_set_wide_entry.num_tossups = qset.num_packets * entry.min_tossups
                                    new_set_wide_entry.num_bonuses = qset.num_packets * entry.min_bonuses
                                    new_set_wide_entry.save()

                entries = dist.distributionentry_set.all()
                initial_data = []
                for entry in entries:
                    initial_data.append({'entry_id': entry.id,
                                         'category': entry.category,
                                         'subcategory': entry.subcategory,
                                         'num_bonuses': entry.min_bonuses,
                                         'num_tossups': entry.max_tossups,})
                formset = TiebreakDistributionEntryFormset(initial=initial_data, prefix='tiebreak')

            else:
                dist = Distribution.objects.get(id=dist_id)
                dist_form = DistributionForm(instance=dist)
                formset = TiebreakDistributionEntryFormset(data=request.POST, prefix='tiebreak')

        return render_to_response('edit_tiebreak.html',
                                  {'form': dist_form,
                                   'formset': formset},
                                   context_instance=RequestContext(request))

    else:
        if dist_id is not None:
            dist = TieBreakDistribution.objects.get(id=dist_id)
            entries = dist.distributionentry_set.all()
            initial_data = []
            for entry in entries:
                initial_data.append({'entry_id': entry.id,
                                     'category': entry.category,
                                     'subcategory': entry.subcategory,
                                     'num_tossups': entry.min_tossups,
                                     'num_bonuses': entry.min_bonuses,})
            dist_form = TieBreakDistributionForm(instance=dist)
            formset = TiebreakDistributionEntryFormset(initial=initial_data, prefix='tiebreak')
        else:
            dist_form = TieBreakDistributionForm()
            formset = TiebreakDistributionEntryFormset(prefix='tiebreak')

        return render_to_response('edit_tiebreak.html',
        {'form': dist_form,
        'formset': formset,},
        context_instance=RequestContext(request))


@login_required
def add_comment(request):

    user = request.user.writer
    qset_id = request.POST['qset-id']
    qset = QuestionSet.objects.get(id=qset_id)

    if request.method == 'POST':

        comment_text = request.POST['comment-text']
        cache.clear()
        print comment_text


@login_required
def upload_questions(request, qset_id):
    qset = QuestionSet.objects.get(id=qset_id)
    user = request.user.writer

    if request.method == 'POST':
        if (user == qset.owner or user in qset.editor.all() or user in qset.writer.all()):
            form = QuestionUploadForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_tossups, uploaded_bonuses = parse_uploaded_packet(request.FILES['questions_file'])
                cache.clear()

                return render_to_response('upload_preview.html',
                {'tossups': uploaded_tossups,
                'bonuses': uploaded_bonuses,
                'message': mark_safe('Please verify that this data is correct. Hitting "Submit" will upload these questions '\
                'If you see any mistakes in the submissions, please correct them in the <strong><em>original file</em></strong> and reupload.'),
                'message_class': 'alert-box warning',
                'qset': qset},
                context_instance=RequestContext(request))
            else:
                messages.error(request, form.questions_file.errors)
                return HttpResponseRedirect('/edit_question_set/{0}'.format(qset_id))
        else:
            messages.error(request, 'You do not have permission to upload ')

@login_required
def type_questions(request, qset_id=None):
    if qset_id is not None:
        qset = QuestionSet.objects.get(id=qset_id)
    else:
        qset = QuestionSet.objects.get(id=request.POST['qset_id'])

    user = request.user.writer

    if request.method == 'POST':
        if (user == qset.owner or user in qset.editor.all() or user in qset.writer.all()):
            form = TypeQuestionsForm(request.POST)
            if form.is_valid():
                question_data = request.POST['questions'].splitlines()
                tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(question_data, qset)

                return render_to_response('type_questions_preview.html',
                                         {'tossups': tossups,
                                          'bonuses': bonuses,
                                          'tossup_errors': tossup_errors,
                                          'bonus_errors': bonus_errors,
                                          'message': 'Please verify that these questions have been correctly parsed. Hitting "Submit" will '\
                                          'commit these questions to the database. If you see any mistakes, hit "Cancel" and correct your mistakes.',
                                          'qset': qset,
                                          'user': user},
                                          context_instance=RequestContext(request))
            else:
                question_data = request.POST['questions']
                tossups, bonuses = parse_packet_data(question_data, qset)
                messages.error(request, form.questions.errors)

        else:
            tossups = None
            bonuses = None
            messages.error(request, 'You do not have permission to add questions to this set')
            return render_to_response('type_questions.html',
                                     {'tossups': tossups,
                                      'bonuses': bonuses,
                                      'qset': qset,
                                      'user': user},
                                      context_instance=RequestContext(request))
    elif request.method == 'GET':
        if (user == qset.owner or user in qset.editor.all() or user in qset.writer.all()):
            dist_entries = qset.setwidedistributionentry_set.all().order_by('dist_entry__category', 'dist_entry__subcategory')

            form = TypeQuestionsForm(request.POST)
            return render_to_response('type_questions.html',
                                     {'user': user,
                                      'qset': qset,
                                      'form': form,
                                      'dist_entries': dist_entries},
                                      context_instance=RequestContext(request))
        else:
            messages.error(request, 'You do not have permission to add questions to this set')
            return render_to_response('type_questions.html',
                                     {'qset': qset,
                                      'user': user},
                                      context_instance=RequestContext(request))

@login_required
def type_questions_edit(request, question_type, question_id):
    user = request.user.writer
    
    if (question_type == "tossup"):
        question = Tossup.objects.get(id=question_id)
    elif (question_type == "bonus"):
        question = Bonus.objects.get(id=question_id)
    
    qset = question.question_set
    packet = question.packet
    message = ''
    message_class = ''
    read_only = True
    role = get_role_no_owner(user, qset)

    if request.method == 'POST':
        if (user == qset.owner or user in qset.editor.all() or user in qset.writer.all()):
            form = TypeQuestionsForm(request.POST)
            if form.is_valid():
                question_data = request.POST['questions'].splitlines()
                tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(question_data, qset)

                return render_to_response('type_questions_edit_preview.html',
                                         {'tossups': tossups,
                                          'bonuses': bonuses,
                                          'tossup_errors': tossup_errors,
                                          'bonus_errors': bonus_errors,
                                          'message': 'Please verify that these questions have been correctly parsed. Hitting "Submit" will '\
                                          'commit these questions to the database. If you see any mistakes, hit "Cancel" and correct your mistakes.',
                                          'qset': qset,
                                          'user': user},
                                          context_instance=RequestContext(request))
            else:
                question_data = request.POST['questions']
                tossups, bonuses = parse_packet_data(question_data, qset)
                messages.error(request, form.questions.errors)

        else:
            tossups = None
            bonuses = None
            messages.error(request, 'You do not have permission to edit this question')
            return render_to_response('type_questions_edit.html',
                                     {'tossups': tossups,
                                      'bonuses': bonuses,
                                      'qset': qset,
                                      'user': user},
                                      context_instance=RequestContext(request))
    elif request.method == 'GET':
        if (user == qset.owner or user in qset.editor.all() or user in qset.writer.all()):
            dist_entries = qset.setwidedistributionentry_set.all().order_by('dist_entry__category', 'dist_entry__subcategory')

            form = TypeQuestionsForm(request.POST)
            return render_to_response('type_questions_edit.html',
                                     {'user': user,
                                      'qset': qset,
                                      'form': form,
                                      'dist_entries': dist_entries},
                                      context_instance=RequestContext(request))
        else:
            messages.error(request, 'You do not have permission to edit this question')
            return render_to_response('type_questions_edit.html',
                                     {'qset': qset,
                                      'user': user},
                                      context_instance=RequestContext(request))

@login_required
def complete_upload(request):
    user = request.user.writer
    if request.method == 'POST':
        qset_id = request.POST['qset-id']
        qset = QuestionSet.objects.get(id=qset_id)

        num_tossups = int(request.POST['num-tossups'])
        num_bonuses = int(request.POST['num-bonuses'])
        categories = DistributionEntry.objects.filter(distribution=qset.distribution)
        questionTypes = QuestionType.objects.all()

        new_tossups = []
        new_bonuses = []

        for tu_num in range(num_tossups):
            data="UTF-8 DATA"
            tu_text_name = 'tossup-text-{0}'.format(tu_num)
            tu_ans_name = 'tossup-answer-{0}'.format(tu_num)
            tu_cat_name = 'tossup-category-{0}'.format(tu_num)
            tu_type_name = 'tossup-type-{0}'.format(tu_num)

            tu_text = strip_markup(request.POST[tu_text_name])
            tu_ans = strip_markup(request.POST[tu_ans_name])
            tu_cat = request.POST[tu_cat_name]
            tu_type = request.POST[tu_type_name]

            new_tossup = Tossup()
            new_tossup.tossup_text = tu_text
            new_tossup.tossup_answer = tu_ans
            new_tossup.author = user
            new_tossup.question_set = qset

            for category in categories:
                formattedCategory = category.category + " - " + category.subcategory
                if (formattedCategory == tu_cat):
                    new_tossup.category = category
                    break

            for questionType in questionTypes:
                if (str(questionType) == tu_type):
                    new_tossup.question_type = questionType
                    break

            new_tossup.locked = False
            new_tossup.edited = False

            new_tossup.save_question(edit_type=QUESTION_CREATE, changer=user)
            new_tossups.append(new_tossup)

        for bs_num in range(num_bonuses):
            bs_leadin_name = 'bonus-leadin-{0}'.format(bs_num)

            bs_part1_name = 'bonus-part1-{0}'.format(bs_num)
            bs_ans1_name = 'bonus-answer1-{0}'.format(bs_num)
            bs_part2_name = 'bonus-part2-{0}'.format(bs_num)
            bs_ans2_name = 'bonus-answer2-{0}'.format(bs_num)
            bs_part3_name = 'bonus-part3-{0}'.format(bs_num)
            bs_ans3_name = 'bonus-answer3-{0}'.format(bs_num)
            bs_cat_name = 'bonus-category-{0}'.format(bs_num)
            bs_type_name = 'bonus-type-{0}'.format(bs_num)
            bs_type = request.POST[bs_type_name]

            new_bonus = Bonus()
            new_bonus.question_set = qset
            new_bonus.author = user
            new_bonus.edited = False
            new_bonus.locked = False
            new_bonus.leadin = strip_markup(request.POST[bs_leadin_name])
            new_bonus.part1_text = strip_markup(request.POST[bs_part1_name])
            new_bonus.part1_answer = strip_markup(request.POST[bs_ans1_name])
            new_bonus.part2_text = strip_markup(request.POST[bs_part2_name])
            new_bonus.part2_answer = strip_markup(request.POST[bs_ans2_name])
            new_bonus.part3_text = strip_markup(request.POST[bs_part3_name])
            new_bonus.part3_answer = strip_markup(request.POST[bs_ans3_name])

            bonus_cat = request.POST[bs_cat_name]
            for category in categories:
                formattedCategory = category.category + " - " + category.subcategory
                if (formattedCategory == bonus_cat):
                    new_bonus.category = category
                    break

            for questionType in questionTypes:
                if (str(questionType) == bs_type):
                    new_bonus.question_type = questionType
                    break

            new_bonus.save_question(edit_type=QUESTION_CREATE, changer=user)
            new_bonuses.append(new_bonus)

        cache.clear()
        messages.success(request, 'Your questions have been uploaded.', extra_tags='alert-box success')        
        for tossup in new_tossups:
            messages.success(request, u'View your tossup on <a href="/edit_tossup/{0}">{1}.</a>'.format(tossup.id, get_answer_no_formatting(tossup.tossup_answer)), extra_tags='safe alert-box info')

        for bonus in new_bonuses:
            messages.success(request, u'View your bonus on <a href="/edit_bonus/{0}">{1}.</a>'.format(bonus.id, get_answer_no_formatting(bonus.part1_answer)), extra_tags='safe alert-box info')

        return HttpResponseRedirect('/edit_question_set/{0}'.format(qset_id))

    else:
        messages.error(request, 'Invalid request!')
        return render_to_response('failure.html')

@login_required
def settings(request):

    if request.method == 'GET':
        return render_to_response('settings.html', {}, context_instance=RequestContext(request))

    else:
        messages.error(request, 'Invalid request!')
        return render_to_response('failure.html', {}, context_instance=RequestContext(request))

@login_required
def profile(request):

    user = request.user
    writer = Writer.objects.get(user=user)

    if request.method == 'GET':
        initial_data = {'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email,
                        'send_mail_on_comments': writer.send_mail_on_comments}

        form = WriterChangeForm(initial=initial_data)

    elif request.method == 'POST':

        print request.POST
        form = WriterChangeForm(request.POST)

        if form.is_valid():
            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            writer.send_mail_on_comments = form.cleaned_data['send_mail_on_comments']
            user.save()
            writer.save()

    return render_to_response('profile.html',
            {'form': form,
             'user': request.user.writer},
            context_instance=RequestContext(request))

@login_required()
def search(request, passed_qset_id=None):

    user = request.user.writer

    passed_q_set = None
    if passed_qset_id is not None:
        passed_q_set = QuestionSet.objects.get(id=passed_qset_id)

    question_sets = QuestionSet.objects.filter(Q(writer=user) | Q(editor=user) | Q(owner=user)).distinct()

    if request.method == 'GET':
        all_categories = [(cat.category, cat.subcategory) for cat in DistributionEntry.objects.all()]
        categories = []
        for cat in all_categories:
            if cat not in categories:
                categories.append(cat)

        if request.GET.dict() == {}:

            q_set = passed_q_set

            return render_to_response('search/search.html',
                                      {'user': user,
                                       'categories': categories,
                                       'q_sets': question_sets,
                                       'selected_qset': q_set,
                                       'tossups_selected': 'checked',
                                       'bonuses_selected': 'checked',
                                       'search_all_selected' :'unchecked',
                                       'passed_q_set': passed_q_set},
                                      context_instance=RequestContext(request))

        else:
            query = request.GET.get('q')
            search_models = request.GET.getlist('models')
            qset_id = int(request.GET.get('qset'))
            qset = QuestionSet.objects.get(id=qset_id)
            search_category = request.GET.get('category')
            tossups_selected = "unchecked"
            bonuses_selected = "unchecked"
            search_all_selected = "unchecked"
            if 'qsub.tossup' in search_models:
                tossups_selected = "checked"
            if 'qsub.bonus' in search_models:
                bonuses_selected = "checked"
            if 'qsub.search_all' in search_models:
                search_all_selected = "checked"

            if user in qset.writer.all() or user in qset.editor.all() or user == qset.owner:
                if search_all_selected == 'checked':
                    search_query_set = SearchQuerySet().filter(question_set__in=question_sets)
                else:
                    search_query_set = SearchQuerySet().filter(question_set=qset)
                search_query_set = search_query_set.filter(Q(question_answers=query) | Q(question_content=query))

                if 'qsub.tossup' in search_models and 'qsub.bonus' not in search_models:
                    result_ids = [r.id for r in search_query_set.models(Tossup)]
                elif 'qsub.bonus' in search_models and 'qsub.tossup' not in search_models:
                    result_ids = [r.id for r in search_query_set.models(Bonus)]
                elif 'qsub.tossup' in search_models and 'qsub.bonus' in search_models:
                    result_ids = [r.id for r in search_query_set.models(Tossup, Bonus)]
                else:
                    result_ids = []

                questions = []
                for q_id in result_ids:
                    try:
                        fields = q_id.split('.')
                        question_type = fields[1]
                        question_id = int(fields[2])
                        if question_type == 'tossup':
                            question = Tossup.objects.get(id=question_id)
                        elif question_type == 'bonus':
                            question = Bonus.objects.get(id=question_id)

                        print(question.question_set == qset)

                        if str(question.category) == search_category or search_category == 'All':
                            questions.append(question)
                    except:
                        print "Error retrieving search data for search query", query, sys.exc_info()[0]

                result = questions
                message = ''
                message_class = ''

            else:
                result = []
                message = 'You are not authorized to view questions from this set.'
                message_class = 'alert-box alert'

            return render_to_response('search/search.html',
                                      {'user': user,
                                       'categories': categories,
                                       'q_sets': question_sets,
                                       'result': result,
                                       'search_term': query,
                                       'search_category': search_category,
                                       'selected_qset': qset,
                                       'tossups_selected': tossups_selected,
                                       'bonuses_selected': bonuses_selected,
                                       'search_all_selected': search_all_selected,
                                       'passed_q_set': passed_q_set,
                                       'message': message,
                                       'message_class': message_class},
                                      context_instance=RequestContext(request))

@login_required
def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/main/")

@login_required
def move_tossup(request, q_set_id, tossup_id):
    user = request.user.writer
    q_set = QuestionSet.objects.get(id=q_set_id)
    role = get_role_no_owner(user, q_set)
    
    tossup = Tossup.objects.get(id=tossup_id)
    if (tossup is None or tossup.question_set != q_set):
        message = 'Invalid tossup'
        message_class = 'alert-box alert'
        tossup = None

    move_sets = user.question_set_editor.exclude(id=q_set_id)

    if request.method == 'GET':
        if (role == "editor"):
            if (tossup is not None):
                form = MoveTossupForm(move_sets=move_sets)

                message = ''
                message_class = ''

                return render_to_response('move_tossup.html',
                                    {'user': user,
                                     'q_set': q_set,
                                     'form': form,
                                     'tossup': tossup,
                                     'message': message,
                                     'message_class': message_class},
                                     context_instance=RequestContext(request))
            else:
                form = []
                return render_to_response('move_tossup.html',
                                    {'user': user,
                                     'q_set': q_set,
                                     'form': form,
                                     'tossup': tossup,
                                     'message': message,
                                     'message_class': message_class},
                                     context_instance=RequestContext(request))
        else:
            form = []
            message = 'You do not have permissions to move this question.'
            message_class = 'alert-box alert'
            q_set = []
            return render_to_response('move_tossup.html',
                                {'user': user,
                                 'q_set': q_set,
                                 'tossup': None,
                                 'form': form,
                                 'message': message,
                                 'message_class': message_class},
                                 context_instance=RequestContext(request))

    else:
        # Update the question set for this tossup
        if (role == 'editor'):
            form = MoveTossupForm(request.POST, move_sets=move_sets)

            if form.is_valid():
                dest_qset_id = request.POST["move_sets"]
                dest_qset = QuestionSet.objects.get(id=dest_qset_id)

                if (tossup is not None and dest_qset is not None):
                    tossup.question_set = dest_qset
                    tossup.packet = None

                    tossup.save()
                    cache.clear()
                    message = "Successfully moved tossup to " + str(dest_qset)
                    message_class = 'alert-box success'
                    return render_to_response('move_tossup_success.html',
                                        {'user': user,
                                         'q_set': q_set,
                                         'dest_q_set': dest_qset,
                                         'tossup': tossup,
                                         'message': message,
                                         'message_class': message_class},
                                         context_instance=RequestContext(request))
                else:
                    message = 'There was an error with your submission.  Hit the back button and make sure you selected a valid question set to move to.'
                    message_class = 'alert-box warning'

                    return render_to_response('move_tossup.html',
                                        {'user': user,
                                         'q_set': q_set,
                                         'form': form,
                                         'tossup': tossup,
                                         'message': message,
                                         'message_class': message_class},
                                         context_instance=RequestContext(request))
            else:
                message = 'There was an error moving your question.  Hit the back button and make sure you selected a valid question set to move to.'
                message_class = 'alert-box warning'
                q_set = []
                return render_to_response('move_tossup.html',
                                    {'user': user,
                                     'q_set': q_set,
                                     'tossup': None,
                                     'form': form,
                                     'message': message,
                                     'message_class': message_class},
                                     context_instance=RequestContext(request))

        else:
            message = 'You do not have permissions to move this question.'
            message_class = 'alert-box alert'
            q_set = []
            form = []
            return render_to_response('move_tossup.html',
                                {'user': user,
                                 'q_set': q_set,
                                 'tossup': None,
                                 'form': form,
                                 'message': message,
                                 'message_class': message_class},
                                 context_instance=RequestContext(request))

@login_required
def move_bonus(request, q_set_id, bonus_id):
    user = request.user.writer
    q_set = QuestionSet.objects.get(id=q_set_id)
    role = get_role_no_owner(user, q_set)

    bonus = Bonus.objects.get(id=bonus_id)
    if (bonus is None or bonus.question_set != q_set):
        message = 'Invalid bonus'
        message_class = 'alert-box alert'
        bonus = None

    move_sets = user.question_set_editor.exclude(id=q_set_id)

    if request.method == 'GET':
        if (role == 'editor'):
            if (bonus is not None):
                form = MoveBonusForm(move_sets=move_sets)

                message = ''
                message_class = ''

                return render_to_response('move_bonus.html',
                                    {'user': user,
                                     'q_set': q_set,
                                     'form': form,
                                     'bonus': bonus,
                                     'message': message,
                                     'message_class': message_class},
                                     context_instance=RequestContext(request))
            else:
                form = []
                return render_to_response('move_bonus.html',
                                    {'user': user,
                                     'q_set': q_set,
                                     'form': form,
                                     'bonus': bonus,
                                     'message': message,
                                     'message_class': message_class},
                                     context_instance=RequestContext(request))
        else:
            form = []
            message = 'You do not have permissions to move this question.'
            message_class = 'alert-box alert'
            q_set = []
            return render_to_response('move_bonus.html',
                                {'user': user,
                                 'q_set': q_set,
                                 'bonus': None,
                                 'form': form,
                                 'message': message,
                                 'message_class': message_class},
                                 context_instance=RequestContext(request))

    else:
        # Update the question set for this bonus
        if (role == 'editor'):
            form = MoveBonusForm(request.POST, move_sets=move_sets)
            if form.is_valid():
                dest_qset_id = request.POST["move_sets"]
                dest_qset = QuestionSet.objects.get(id=dest_qset_id)

                if (bonus is not None and dest_qset is not None):
                    bonus.question_set = dest_qset
                    bonus.packet = None

                    bonus.save()
                    cache.clear()
                    return render_to_response('move_bonus_success.html',
                                        {'user': user,
                                         'q_set': q_set,
                                         'dest_q_set': dest_qset,
                                         'bonus': bonus},
                                         context_instance=RequestContext(request))
                else:
                    message = 'There was an error with your submission.  Hit the back button and make sure you selected a valid question set to move to.'
                    message_class = 'alert-box warning'

                    return render_to_response('move_bonus.html',
                                        {'user': user,
                                         'q_set': q_set,
                                         'form': form,
                                         'bonus': bonus,
                                         'message': message,
                                         'message_class': message_class},
                                         context_instance=RequestContext(request))
            else:
                message = 'There was an error moving your question.  Hit the back button and make sure you selected a valid question set to move to.'
                message_class = 'alert-box warning'
                q_set = []
                return render_to_response('move_bonus.html',
                                    {'user': user,
                                     'q_set': q_set,
                                     'bonus': None,
                                     'form': form,
                                     'message': message,
                                     'message_class': message_class},
                                     context_instance=RequestContext(request))

        else:
            message = 'You do not have permissions to move this question.'
            message_class = 'alert-box alert'
            q_set = []
            form = []
            return render_to_response('move_bonus.html',
                                {'user': user,
                                 'q_set': q_set,
                                 'bonus': None,
                                 'form': form,
                                 'message': message,
                                 'message_class': message_class},
                                 context_instance=RequestContext(request))

@login_required
def export_question_set(request, qset_id, output_format):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    role = get_role_no_owner(user, qset)
    
    tossup_content_type_id = ContentType.objects.get_for_model(Tossup).id
    bonus_content_type_id = ContentType.objects.get_for_model(Bonus).id

    if request.method == 'GET':
        if (role == 'editor'):
            if (output_format == "csv"):
                tossups = Tossup.objects.filter(question_set=qset)
                bonuses = Bonus.objects.filter(question_set=qset)

                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="packet2.csv"'

                writer = unicodecsv.writer(response, encoding='utf-8', quoting=csv.QUOTE_ALL)

                writer.writerow(["Tossup Question", "Answer", "Category", "Author", "Edited", "Packet", "Question Number", "Comments","Id", "Editor", "Proofreader", "Read Carefully"])
                for tossup in tossups:
                    comment_list = Comment.objects.filter(content_type_id=tossup_content_type_id).filter(object_pk=tossup.id).filter(is_removed=False).order_by('submit_date')
                    comment_string = ""
                    for comment in comment_list:
                        comment_string = comment_string + str(comment.user) + ": " + comment.comment + "||"
                    
                    editor = ""
                    if tossup.edited:
                        editor = tossup.editor.get_real_name()
                        
                    proofreader = ""
                    if tossup.proofread:
                        proofreader = tossup.proofreader.get_real_name()
                    writer.writerow([remove_new_lines(tossup.tossup_text), remove_new_lines(tossup.tossup_answer), tossup.category, tossup.author.get_real_name(), tossup.edited, tossup.packet, tossup.question_number, remove_new_lines(comment_string), tossup.id, editor, proofreader, tossup.read_carefully])

                writer.writerow([])

                writer.writerow(["Bonus Leadin", "Bonus Part 1", "Bonus Answer 1", "Bonus Part 2", "Bonus Answer 2", "Bonus Part 3", "Bonus Answer 3", "Category", "Author", "Edited", "Packet", "Question Number", "Comments", "Id", "Editor", "Proofreader", "Read Carefully"])
                for bonus in bonuses:
                    comment_list = Comment.objects.filter(content_type_id=bonus_content_type_id).filter(object_pk=bonus.id).filter(is_removed=False).order_by('submit_date')
                    comment_string = ""
                    for comment in comment_list:
                        comment_string = comment_string + str(comment.user) + ": " + comment.comment + "||"

                    editor = ""
                    if bonus.edited:
                        editor = bonus.editor.get_real_name()
                        
                    proofreader = ""
                    if bonus.proofread:
                        proofreader = bonus.proofreader.get_real_name()
                    
                    writer.writerow([remove_new_lines(bonus.leadin), remove_new_lines(bonus.part1_text), remove_new_lines(bonus.part1_answer), remove_new_lines(bonus.part2_text), remove_new_lines(bonus.part2_answer), remove_new_lines(bonus.part3_text), remove_new_lines(bonus.part3_answer), bonus.category, bonus.author.get_real_name(), bonus.edited, bonus.packet, bonus.question_number, remove_new_lines(comment_string), bonus.id,  editor, proofreader, bonus.read_carefully])
                    
                writer.writerow([])
                entries = qset.setwidedistributionentry_set.all()                
                writer.writerow(["Category", "Subcategory", "Total Tossups", "Total Bonuses"])
                for entry in entries:
                    writer.writerow([entry.dist_entry.category, entry.dist_entry.subcategory, entry.num_tossups, entry.num_bonuses])

                return response
            elif (output_format == "pdf"):
                # TODO: Experiment with one of those PDF libraries
                message = 'Not supported yet.'
                message_class = 'alert-box alert'
                q_set = []
                tossups = []
                bonuses = []
                return render_to_response('export_question_set.html',
                                    {'user': user,
                                     'q_set': q_set,
                                     'tossups': tossups,
                                     'bonuses': bonuses,
                                     'message': message,
                                     'message_class': message_class},
                                     context_instance=RequestContext(request))
            else:
                message = 'Unsupported export format.'
                message_class = 'alert-box alert'
                q_set = []
                tossups = []
                bonuses = []
                return render_to_response('export_question_set.html',
                                    {'user': user,
                                     'q_set': q_set,
                                     'tossups': tossups,
                                     'bonuses': bonuses,
                                     'message': message,
                                     'message_class': message_class},
                                     context_instance=RequestContext(request))

        else:
            message = 'You are not authorized to export questions from this set.'
            message_class = 'alert-box alert'
            q_set = []
            tossups = []
            bonuses = []
            return render_to_response('export_question_set.html',
                                {'user': user,
                                 'q_set': q_set,
                                 'tossups': tossups,
                                 'bonuses': bonuses,
                                 'message': message,
                                 'message_class': message_class},
                                 context_instance=RequestContext(request))

@login_required
def restore_tossup(request):
    user = request.user.writer

    message = ''
    message_class = ''
    read_only = True

    if request.method == 'POST':
        th_id = request.POST['th_id']
        tossup_history = TossupHistory.objects.get(id=th_id)
        tossup = Tossup.objects.get(question_history=tossup_history.question_history)
        if (tossup_history is None):
            message = 'Invalid tossup history restoration!'
            message_class = 'alert-box warning'
        else:
            qset_id = request.POST['qset_id']
            qset = QuestionSet.objects.get(id=qset_id)
            if user == tossup.author or user == qset.owner or user in qset.editor.all():
                tossup = Tossup.objects.get(question_history=tossup_history.question_history)
                if (tossup is None):
                    message = 'Invalid tossup restoration!'
                    message_class = 'alert-box warning'
                else:
                    tossup.tossup_answer = tossup_history.tossup_answer
                    tossup.tossup_text = tossup_history.tossup_text
                    tossup.save_question(edit_type=QUESTION_RESTORE, changer=user)
                    cache.clear()
                    message = 'Successfully restored question'
                    message_class = 'alert-box success'
            else:
                message = 'You are not authorized to restore this question!'
                message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def restore_bonus(request):
    user = request.user.writer

    message = ''
    message_class = ''
    read_only = True

    if request.method == 'POST':
        bh_id = request.POST['bh_id']
        bonus_history = BonusHistory.objects.get(id=bh_id)
        bonus = Bonus.objects.get(question_history=bonus_history.question_history)
        if (bonus_history is None):
            message = 'Invalid bonus history restoration!'
            message_class = 'alert-box warning'
        else:
            qset_id = request.POST['qset_id']
            qset = QuestionSet.objects.get(id=qset_id)
            if user == bonus.author or user == qset.owner or user in qset.editor.all():
                bonus = Bonus.objects.get(question_history=bonus_history.question_history)
                if (bonus is None):
                    message = 'Invalid bonus restoration!'
                    message_class = 'alert-box warning'
                else:
                    bonus.question_type = bonus_history.question_type
                    bonus.leadin = bonus_history.leadin
                    bonus.part1_text = bonus_history.part1_text
                    bonus.part1_answer = bonus_history.part1_answer
                    bonus.part2_text = bonus_history.part2_text
                    bonus.part2_answer = bonus_history.part2_answer
                    bonus.part3_text = bonus_history.part3_text
                    bonus.part3_answer = bonus_history.part3_answer
                    bonus.save_question(edit_type=QUESTION_RESTORE, changer=user)
                    cache.clear()
                    message = 'Successfully restored question'
                    message_class = 'alert-box success'
            else:
                message = 'You are not authorized to restore this question!'
                message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def tossup_history(request, tossup_id):
    user = request.user.writer
    if request.method == 'GET':
        tossup = Tossup.objects.get(id=tossup_id)
        if (tossup is None):
            message = 'Invalid tossup'
            message_class = 'alert-box alert'
            tossup = None
        else:
            q_set = tossup.question_set
            if (q_set is None):
                message = 'Invalid question set'
                message_class = 'alert-box alert'
                tossup = None
            else:
                q_set_writers = Writer.objects.filter(Q(question_set_writer=q_set) | Q(question_set_editor=q_set)).distinct()
                if (user in q_set_writers):
                    tossup_histories, bonus_histories = tossup.get_question_history()
                    tossup_histories = tossup_histories.order_by('-id')
                    bonus_histories = bonus_histories.order_by('-id')
                    message = ''
                    message_class = ''

                    return render_to_response('tossup_history.html',
                                        {'user': user,
                                         'qset': q_set,
                                         'tossup': tossup,
                                         'tossup_histories': tossup_histories,
                                         'bonus_histories': bonus_histories,
                                         'message': message,
                                         'message_class': message_class},
                                         context_instance=RequestContext(request))

                else:
                    message = "You don't have permission to view this question"
                    message_class = 'alert-box alert'
                    tossup = None


    return render_to_response('tossup_history.html',
                        {'user': user,
                         'q_set': q_set,
                         'tossup': tossup,
                         'tossup_histories': [],
                         'bonus_histories': [],
                         'message': message,
                         'message_class': message_class},
                         context_instance=RequestContext(request))

@login_required
def bonus_history(request, bonus_id):
    user = request.user.writer
    if request.method == 'GET':
        bonus = Bonus.objects.get(id=bonus_id)
        if (bonus is None):
            message = 'Invalid bonus'
            message_class = 'alert-box alert'
            bonus = None
        else:
            q_set = bonus.question_set
            if (q_set is None):
                message = 'Invalid question set'
                message_class = 'alert-box alert'
                bonus = None
            else:
                q_set_writers = Writer.objects.filter(Q(question_set_writer=q_set) | Q(question_set_editor=q_set)).distinct()
                if (user in q_set_writers):
                    message = ''
                    message_class = ''

                    tossup_histories, bonus_histories = bonus.get_question_history()
                    tossup_histories = tossup_histories.order_by('-id')
                    bonus_histories = bonus_histories.order_by('-id')
                    return render_to_response('bonus_history.html',
                                        {'user': user,
                                         'qset': q_set,
                                         'bonus': bonus,
                                         'tossup_histories': tossup_histories,
                                         'bonus_histories': bonus_histories,
                                         'message': message,
                                         'message_class': message_class},
                                         context_instance=RequestContext(request))

                else:
                    message = "You don't have permission to view this question"
                    message_class = 'alert-box alert'
                    bonus = None


    return render_to_response('bonus_history.html',
                        {'user': user,
                         'q_set': q_set,
                         'bonus': bonus,
                         'tossup_histories': [],
                         'bonus_histories': [],
                         'message': message,
                         'message_class': message_class},
                         context_instance=RequestContext(request))

@login_required
def convert_tossup(request):
    user = request.user.writer

    message = ''
    message_class = ''
    read_only = True

    if request.method == 'POST':
        tossup_id = request.POST['tossup_id']
        tossup = Tossup.objects.get(id=tossup_id)
        if (tossup is None):
            message = 'Invalid tossup!'
            message_class = 'alert-box warning'
        else:
            qset_id = request.POST['qset_id']
            qset = QuestionSet.objects.get(id=qset_id)
            if user == tossup.author or user == qset.owner or user in qset.editor.all():
                target_type = request.POST['target_type']
                if (target_type == ACF_STYLE_TOSSUP):
                    tossup_to_tossup(tossup, target_type)
                else:
                    tossup_to_bonus(tossup, target_type)

                message = 'Successfully changed tossup type'
                message_class = 'alert-box success'
                cache.clear()
            else:
                message = 'You are not authorized to change this tossup type!'
                message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def convert_bonus(request):
    user = request.user.writer

    message = ''
    message_class = ''
    read_only = True

    if request.method == 'POST':
        bonus_id = request.POST['bonus_id']
        bonus = Bonus.objects.get(id=bonus_id)
        if (bonus is None):
            message = 'Invalid bonus!'
            message_class = 'alert-box warning'
        else:
            qset_id = request.POST['qset_id']
            qset = QuestionSet.objects.get(id=qset_id)
            if user == bonus.author or user == qset.owner or user in qset.editor.all():
                target_type = request.POST['target_type']
                if (target_type == ACF_STYLE_BONUS or target_type == VHSL_BONUS):
                    bonus_to_bonus(bonus, target_type)
                else:
                    bonus_to_tossup(bonus, target_type)

                message = 'Successfully changed bonus type'
                message_class = 'alert-box success'
                cache.clear()
            else:
                message = 'You are not authorized to change this bonus type!'
                message_class = 'alert-box warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def questions_remaining(request, qset_id):
    message = ''

    qset = QuestionSet.objects.get(id=qset_id)
    user = request.user.writer
    set_status = {}

    total_tu_req = 0
    total_bs_req = 0
    total_tu_written = 0
    total_bs_written = 0
    tu_needed = 0
    bs_needed = 0

    role = get_role_no_owner(user, qset)

    if role == 'none':
        messages.error(request, 'You are not authorized to view information about this tournament!')
        return HttpResponseRedirect('/failure.html/')

    if request.method == 'GET':
        set_status, total_tu_req, total_bs_req, tu_needed, bs_needed, set_pct_complete = get_questions_remaining(qset)

    return render_to_response('questions_remaining.html',
                             {'user': user,
                              'set_status': set_status,
                              'set_pct_complete': '{0:0.2f}%'.format(set_pct_complete),
                              'set_pct_progress_bar': '{0:0.0f}%'.format(set_pct_complete),
                              'tu_needed': tu_needed,
                              'bs_needed': bs_needed,
                              'qset': qset,
                              'message': message},
                              context_instance=RequestContext(request))

@login_required
def bulk_change_set(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    qset_editors = qset.editor.all()
    qset_writers = qset.writer.all()

    message = ''
    message_class = ''
    tossups = []
    bonuses = []
    role = get_role_no_owner(user, qset)

    if role != 'editor':
        message = 'You are not authorized to make bulk operations on this set'
        return HttpResponseRedirect('/failure.html/')
    else:
        tossups = Tossup.objects.filter(question_set=qset).order_by('-id')
        bonuses = Bonus.objects.filter(question_set=qset).order_by('-id')

    if request.method == 'GET':
        return render_to_response('bulk_change_set.html',
                                 {'user': user,
                                  'tossups': tossups,
                                  'bonuses': bonuses,
                                  'qset': qset,
                                  'message': message,
                                  'message_class': message_class},
                                 context_instance=RequestContext(request))
    else:
        if ('confirm' in request.POST):
            operation = request.POST['change-type']
            if (operation == "author-step2"):
                return bulk_change_author(request, qset_id)
            elif (operation == "move-step2"):
                return bulk_move_question(request, qset_id)
            elif (operation == "packet-step2"):
                return bulk_change_packet(request, qset_id)

            num_questions_selected = 0
            num_tossups = int(request.POST['num-tossups'])
            num_bonuses = int(request.POST['num-bonuses'])

            change_tossups = []
            change_bonuses = []

            for tu_num in range(num_tossups):
                tu_checked_name = 'tossup-checked-{0}'.format(tu_num)
                tu_id_name = 'tossup-id-{0}'.format(tu_num)

                if (tu_checked_name in request.POST):
                    tu_id = request.POST[tu_id_name]
                    tossup = Tossup.objects.get(id=tu_id)
                    change_tossups.append(tossup)
                    num_questions_selected += 1

            for bs_num in range(num_bonuses):
                bs_checked_name = 'bonus-checked-{0}'.format(bs_num)
                bs_id_name = 'bonus-id-{0}'.format(bs_num)

                if (bs_checked_name in request.POST):
                    bs_id = request.POST[bs_id_name]
                    bonus = Bonus.objects.get(id=bs_id)
                    change_bonuses.append(bonus)
                    num_questions_selected += 1

            if (num_questions_selected > 0):
                # Do the actual operation

                if (operation == 'edit'):
                    bulk_edit_questions(True, change_tossups, change_bonuses, qset, user)

                    message = "Successfully edited questions."
                    message_class = 'alert-box success'
                    cache.clear()
                    return render_to_response('bulk_change_set.html',
                                             {'user': user,
                                              'tossups': tossups,
                                              'bonuses': bonuses,
                                              'qset': qset,
                                              'message': message,
                                              'message_class': message_class},
                                             context_instance=RequestContext(request))
                elif (operation == 'unedit'):
                    bulk_edit_questions(False, change_tossups, change_bonuses, qset, user)

                    message = "Successfully unedited questions."
                    message_class = 'alert-box success'
                    cache.clear()
                    return render_to_response('bulk_change_set.html',
                                             {'user': user,
                                              'tossups': tossups,
                                              'bonuses': bonuses,
                                              'qset': qset,
                                              'message': message,
                                              'message_class': message_class},
                                             context_instance=RequestContext(request))
                elif (operation == 'packet'):
                    packets = Packet.objects.filter(question_set=qset)
                    
                    cache.clear()
                    return render_to_response('bulk_change_packet.html',
                                             {'user': user,
                                              'tossups': change_tossups,
                                              'bonuses': change_bonuses,
                                              'qset': qset,
                                              'message': message,
                                              'message_class': message_class},
                                             context_instance=RequestContext(request))
                elif (operation == 'lock'):
                    bulk_lock_questions(True, change_tossups, change_bonuses, qset, user)

                    message = "Successfully locked questions."
                    message_class = 'alert-box success'
                    cache.clear()
                    return render_to_response('bulk_change_set.html',
                                             {'user': user,
                                              'tossups': tossups,
                                              'bonuses': bonuses,
                                              'qset': qset,
                                              'message': message,
                                              'message_class': message_class},
                                             context_instance=RequestContext(request))
                elif (operation == 'unlock'):
                    bulk_lock_questions(False, change_tossups, change_bonuses, qset, user)

                    message = "Successfully unlocked questions."
                    message_class = 'alert-box success'
                    cache.clear()
                    return render_to_response('bulk_change_set.html',
                                             {'user': user,
                                              'tossups': tossups,
                                              'bonuses': bonuses,
                                              'qset': qset,
                                              'message': message,
                                              'message_class': message_class},
                                             context_instance=RequestContext(request))
                elif (operation == 'delete'):
                    bulk_delete_questions(change_tossups, change_bonuses, qset, user)
                    message = "Successfully deleted questions."
                    message_class = 'alert-box success'
                    cache.clear()
                    tossups = Tossup.objects.filter(question_set=qset).order_by('-id')
                    bonuses = Bonus.objects.filter(question_set=qset).order_by('-id')

                    return render_to_response('bulk_change_set.html',
                                             {'user': user,
                                              'tossups': tossups,
                                              'bonuses': bonuses,
                                              'qset': qset,
                                              'message': message,
                                              'message_class': message_class},
                                             context_instance=RequestContext(request))

                elif (operation == 'convert-to-acf-style-tossup'):
                    bulk_convert_to_acf_style_tossup(change_tossups, change_bonuses, qset, user)
                    message = "Successfully converted question type to ACF-style tossups."
                    message_class = 'alert-box success'
                    cache.clear()
                    tossups = Tossup.objects.filter(question_set=qset).order_by('-id')
                    bonuses = Bonus.objects.filter(question_set=qset).order_by('-id')

                    return render_to_response('bulk_change_set.html',
                                             {'user': user,
                                              'tossups': tossups,
                                              'bonuses': bonuses,
                                              'qset': qset,
                                              'message': message,
                                              'message_class': message_class},
                                             context_instance=RequestContext(request))

                elif (operation == 'convert-to-acf-style-bonus'):
                    bulk_convert_to_acf_style_bonus(change_tossups, change_bonuses, qset, user)
                    message = "Successfully converted question type to ACF-style bonuses."
                    message_class = 'alert-box success'
                    cache.clear()
                    tossups = Tossup.objects.filter(question_set=qset).order_by('-id')
                    bonuses = Bonus.objects.filter(question_set=qset).order_by('-id')

                    return render_to_response('bulk_change_set.html',
                                             {'user': user,
                                              'tossups': tossups,
                                              'bonuses': bonuses,
                                              'qset': qset,
                                              'message': message,
                                              'message_class': message_class},
                                             context_instance=RequestContext(request))
                elif (operation == 'convert-to-vhsl-bonus'):
                    bulk_convert_to_vhsl_bonus(change_tossups, change_bonuses, qset, user)
                    message = "Successfully converted question type to VHSL bonuses."
                    message_class = 'alert-box success'
                    cache.clear()

                    tossups = Tossup.objects.filter(question_set=qset).order_by('-id')
                    bonuses = Bonus.objects.filter(question_set=qset).order_by('-id')

                    return render_to_response('bulk_change_set.html',
                                             {'user': user,
                                              'tossups': tossups,
                                              'bonuses': bonuses,
                                              'qset': qset,
                                              'message': message,
                                              'message_class': message_class},
                                             context_instance=RequestContext(request))
                elif (operation == 'move'):
                    new_sets = user.question_set_editor.exclude(id=qset_id)
                    cache.clear()
                    return render_to_response('bulk_move_questions.html',
                                             {'user': user,
                                              'tossups': change_tossups,
                                              'bonuses': change_bonuses,
                                              'qset': qset,
                                              'new_sets': new_sets,
                                              'message': message,
                                              'message_class': message_class},
                                             context_instance=RequestContext(request))
                elif (operation == 'author'):
                    writers = Writer.objects.filter(Q(question_set_writer=qset) | Q(question_set_editor=qset)).distinct()
                    cache.clear()

                    return render_to_response('bulk_change_author.html',
                                             {'user': user,
                                              'tossups': change_tossups,
                                              'bonuses': change_bonuses,
                                              'qset': qset,
                                              'writers': writers,
                                              'message': message,
                                              'message_class': message_class},
                                             context_instance=RequestContext(request))

            else:
                message = "Error!  You must select at least one question."
                message_class = 'alert-box warning'
                return render_to_response('bulk_change_set.html',
                                         {'user': user,
                                          'tossups': tossups,
                                          'bonuses': bonuses,
                                          'qset': qset,
                                          'message': message,
                                          'message_class': message_class},
                                         context_instance=RequestContext(request))
        else:
            message = "You didn't hit the confirm button."
            message_class = 'alert-box warning'
            return render_to_response('bulk_change_set.html',
                                     {'user': user,
                                      'tossups': tossups,
                                      'bonuses': bonuses,
                                      'qset': qset,
                                      'message': message,
                                      'message_class': message_class},
                                     context_instance=RequestContext(request))

@login_required
def bulk_change_author(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)

    message = ''
    message_class = ''
    read_only = True

    role = get_role_no_owner(user, qset)

    if role != 'editor':
        message = 'You are not authorized to make bulk operations on this set'
        return HttpResponseRedirect('/failure.html/')

    if request.method == 'POST':
        num_tossups = int(request.POST['num-tossups'])
        num_bonuses = int(request.POST['num-bonuses'])
        new_author_id = request.POST['new-author']
        new_author = Writer.objects.get(id=new_author_id)

        new_author_role = get_role_no_owner(new_author, qset)
        if (new_author_role == 'none'):
            message = 'Could not change author to ' + str(new_author)
            return HttpResponseRedirect('/failure.html/')

        for tu_num in range(num_tossups):
            tu_id_name = 'tossup-id-{0}'.format(tu_num)
            tu_id = request.POST[tu_id_name]
            tossup = Tossup.objects.get(id=tu_id)
            tossup.author = new_author
            tossup.save()

        for bs_num in range(num_bonuses):
            bs_id_name = 'bonus-id-{0}'.format(bs_num)
            bs_id = request.POST[bs_id_name]
            bonus = Bonus.objects.get(id=bs_id)
            bonus.author = new_author
            bonus.save()

        message = 'Successfully changed author'
        message_class = 'alert-box success'
        cache.clear()

        tossups = Tossup.objects.filter(question_set=qset).order_by('-id')
        bonuses = Bonus.objects.filter(question_set=qset).order_by('-id')

        return render_to_response('bulk_change_set.html',
                                 {'user': user,
                                  'tossups': tossups,
                                  'bonuses': bonuses,
                                  'qset': qset,
                                  'message': message,
                                  'message_class': message_class},
                                 context_instance=RequestContext(request))

@login_required
def bulk_change_packet(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)

    message = ''
    message_class = ''
    read_only = True

    role = get_role_no_owner(user, qset)

    if role != 'editor':
        message = 'You are not authorized to make bulk operations on this set'
        return HttpResponseRedirect('/failure.html/')

    if request.method == 'POST':
        num_tossups = int(request.POST['num-tossups'])
        num_bonuses = int(request.POST['num-bonuses'])
        new_packet_id = request.POST['new-packet']
        new_packet = Packet.objects.get(id=new_packet_id)

        # TODO: We may want to clear the numbers from these questions in the future
        for tu_num in range(num_tossups):
            tu_id_name = 'tossup-id-{0}'.format(tu_num)
            tu_id = request.POST[tu_id_name]
            tossup = Tossup.objects.get(id=tu_id)
            tossup.packet = new_packet
            tossup.save()

        for bs_num in range(num_bonuses):
            bs_id_name = 'bonus-id-{0}'.format(bs_num)
            bs_id = request.POST[bs_id_name]
            bonus = Bonus.objects.get(id=bs_id)
            bonus.packet = new_packet
            bonus.save()

        message = 'Successfully changed packet'
        message_class = 'alert-box success'
        cache.clear()

        tossups = Tossup.objects.filter(question_set=qset).order_by('-id')
        bonuses = Bonus.objects.filter(question_set=qset).order_by('-id')

        return render_to_response('bulk_change_set.html',
                                 {'user': user,
                                  'tossups': tossups,
                                  'bonuses': bonuses,
                                  'qset': qset,
                                  'message': message,
                                  'message_class': message_class},
                                 context_instance=RequestContext(request))

@login_required
def bulk_move_question(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)

    message = ''
    message_class = ''
    read_only = True

    role = get_role_no_owner(user, qset)

    if role != 'editor':
        message = 'You are not authorized to make bulk operations on this set'
        return HttpResponseRedirect('/failure.html/')

    if request.method == 'POST':
        num_tossups = int(request.POST['num-tossups'])
        num_bonuses = int(request.POST['num-bonuses'])
        new_set_id = request.POST['new-set']
        new_set = QuestionSet.objects.get(id=new_set_id)

        new_set_role = get_role_no_owner(user, new_set)
        if (new_set_role != 'editor'):
            message = 'Could not move questions to ' + str(new_set)
            return HttpResponseRedirect('/failure.html/')

        for tu_num in range(num_tossups):
            tu_id_name = 'tossup-id-{0}'.format(tu_num)
            tu_id = request.POST[tu_id_name]
            tossup = Tossup.objects.get(id=tu_id)

            tossup.question_set = new_set
            tossup.packet = None

            # It's not guaranteed that these categories exist, so clear them
            tossup.category = None
            tossup.subtype = ''

            tossup.save()

        for bs_num in range(num_bonuses):
            bs_id_name = 'bonus-id-{0}'.format(bs_num)
            bs_id = request.POST[bs_id_name]
            bonus = Bonus.objects.get(id=bs_id)

            bonus.question_set = new_set
            bonus.packet = None

            # It's not guaranteed that these categories exist, so clear them
            bonus.category = None
            bonus.subtype = ''

            bonus.save()

        message = 'Successfully moved questions'
        message_class = 'alert-box success'
        cache.clear()

        tossups = Tossup.objects.filter(question_set=qset).order_by('-id')
        bonuses = Bonus.objects.filter(question_set=qset).order_by('-id')

        return render_to_response('bulk_change_set.html',
                                 {'user': user,
                                  'tossups': tossups,
                                  'bonuses': bonuses,
                                  'qset': qset,
                                  'message': message,
                                  'message_class': message_class},
                                 context_instance=RequestContext(request))

@login_required
def writer_question_set_settings(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)

    message = ''
    message_class = ''

    role = get_role_no_owner(user, qset)
    if (role == 'none'):
        return render_to_response('failure.html',
            {'message': 'You do not have permissions to this set',
             'message_class': 'alert-box alert'},
            context_instance=RequestContext(request))
    
    # Create the settings if it doesn't exist
    settings = None
    try:
        settings = WriterQuestionSetSettings.objects.get(question_set=qset, writer=user)        
    except:
        settings = WriterQuestionSetSettings(writer=user, question_set=qset)
        settings.save()
        settings.create_per_category_writer_settings()
        
    if request.method == 'POST':
        form = WriterQuestionSetSettingsForm(request.POST)

        PerCategoryWriterSettingsFormset = formset_factory(PerCategoryWriterSettingsForm, can_delete=False, extra=0)
        formset = PerCategoryWriterSettingsFormset(data=request.POST)

        if (form.is_valid() and formset.is_valid()):
            settings.email_on_all_new_comments = form.cleaned_data['email_on_all_new_comments']
            settings.email_on_all_new_questions = form.cleaned_data['email_on_all_new_questions']
            settings.save()
            
            for per_category_form in formset.forms:
                entry_id = int(per_category_form.cleaned_data['entry_id'])
                email_on_new_questions = bool(per_category_form.cleaned_data['email_on_new_questions'])
                email_on_new_comments = bool(per_category_form.cleaned_data['email_on_new_comments'])

                entry = PerCategoryWriterSettings.objects.get(id=entry_id)
                entry.email_on_new_questions = email_on_new_questions
                entry.email_on_new_comments = email_on_new_comments
                entry.save()

            message = 'Your settings have been updated.'
            message_class = 'alert-box success'

            return render_to_response('writer_question_set_settings.html',
                     {'form': form,
                     'formset': formset,
                     'message': message,
                     'message_class': message_class,
                     'user': user,
                     'qset': qset},
                     context_instance=RequestContext(request))
            
        else:
            message = 'There was an error saving your settings.'
            message_class = 'alert-box warning'
            return render_to_response('writer_question_set_settings.html',
                     {'form': form,
                     'formset': formset,
                     'message': message,
                     'message_class': message_class,
                     'user': user,
                     'qset': qset},
                     context_instance=RequestContext(request))
        
    elif request.method == 'GET':
        entries = settings.percategorywritersettings_set.all()
        initial_data = []
        for entry in entries:
            initial_data.append({
                'entry_id': entry.id,
                'distribution_entry_string': str(entry.distribution_entry),
                'email_on_new_questions': entry.email_on_new_questions,
                'email_on_new_comments': entry.email_on_new_comments})
                
        form = WriterQuestionSetSettingsForm(instance=settings)
        PerCategoryWriterSettingsFormset = formset_factory(PerCategoryWriterSettingsForm, can_delete=False, extra=0)
        formset = PerCategoryWriterSettingsFormset(initial=initial_data)
                
        return render_to_response('writer_question_set_settings.html',
                                 {'form': form,
                                  'formset': formset,
                                  'message': message,
                                  'message_class': message_class,
                                  'user': user,
                                  'qset': qset},
                                  context_instance=RequestContext(request))

@login_required
def contributor(request, qset_id, writer_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    qset_editors = qset.editor.all()
    qset_writers = qset.writer.all()

    writer = Writer.objects.get(id=writer_id)
    
    tossups = []
    bonuses = []

    
    if (writer not in qset_editors and writer != qset.owner and writer not in qset.writer.all()):
        return render_to_response('failure.html',
            {'message': 'The specified contributor is not in this set',
             'message_class': 'alert-box alert'},
            context_instance=RequestContext(request))
        
    if user not in qset_editors and user != qset.owner and user not in qset.writer.all():
        return render_to_response('failure.html',
            {'message': 'You are not authorized to view this set',
             'message_class': 'alert-box alert'},
            context_instance=RequestContext(request))

    tossups = Tossup.objects.filter(question_set=qset).filter(author=writer)
    bonuses = Bonus.objects.filter(question_set=qset).filter(author=writer)

    writer_status =   {'tossups_written': tossups.count(),
                         'bonuses_written': bonuses.count()
                         }
            
            
    return render_to_response('contributor.html',
        {
        'user': user,
        'tossups': tossups,
        'bonuses': bonuses,
        'writer_status': writer_status,
        'qset': qset,
        'writer': writer},
        context_instance=RequestContext(request))	
