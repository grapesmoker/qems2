import json

from django.template.loader import get_template
from django.template import Context, RequestContext
from django.shortcuts import render_to_response
from django import forms
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from models import *
from forms import *
from model_utils import *
from utils import sanitize_html
from packet_parser import handle_uploaded_packet
from django.utils.safestring import mark_safe

from collections import OrderedDict
from itertools import chain


def register (request):
    if request.method == 'POST':
        form = WriterCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_user = authenticate(username=form.cleaned_data['username'],
                                     password=form.cleaned_data['password1'])
            if auth_user.is_active:
                print 'foo'
                login(request, auth_user)
                return HttpResponseRedirect("/main/")
            else:
                render_to_response('failure.html', {'message': 'Account disabled! Contact administrator!'})
    else:
        form = WriterCreationForm()
    return render_to_response('registration/register.html',
                              {'form': form,},
                              context_instance=RequestContext(request))

@login_required
def main (request):

    return render_to_response('main.html', {'user': request.user.writer},
                              context_instance=RequestContext(request))

@login_required
def question_sets (request):
    writer = request.user.writer

    # all the tournaments owned by this user
    owned_sets = QuestionSet.objects.filter(owner=writer)
    # the tournaments for which this user is an editor
    editor_sets = writer.question_set_editor.all()
    # the tournaments for which this user is a writer
    writer_sets = writer.question_set_writer.all()

    print writer
    print owned_sets

    all_sets  = [{'header': 'Question sets you own', 'qsets': owned_sets, 'id': 'qsets-owned'},
                 {'header': 'Question sets you are editing', 'qsets': editor_sets, 'id': 'qsets-edit'},
                 {'header': 'Question sets you are writing for', 'qsets': writer_sets, 'id': 'qsets-write'}]

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

            set_distro_formset = create_set_distro_formset(question_set)
            tiebreak_formset = create_tiebreak_formset(question_set)

            return render_to_response('edit_question_set.html',
                                      {'message': 'Your question set has been successfully created!',
                                       'message_class': 'alert alert-success',
                                       'qset': question_set,
                                       'user': user,
                                       'form': form,
                                       'set_distro_formset': set_distro_formset,
                                       'tiebreak_formset': tiebreak_formset,
                                       'editors': [ed for ed in question_set.editor.all() if ed != question_set.owner],
                                       'writers': question_set.writer.all(),
                                       'tossups': Tossup.objects.filter(question_set=question_set),
                                       'bonuses': Bonus.objects.filter(question_set=question_set),
                                       'packets': question_set.packet_set.all(),},
                                      context_instance=RequestContext(request))
        else:
            print form.errors
            distributions = Distribution.objects.all()
            return render_to_response('create_question_set.html',
                                      {'message': 'There was an error in creating your question set!',
                                       'message_class': 'alert alert-warning',
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
    print qset_id
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

    total_tu_req = 0
    total_bs_req = 0
    total_tu_written = 0
    total_bs_written = 0

    role = get_role(user, qset)

    if user != qset.owner and user not in qset_editors and user not in qset_writers:
        messages.error(request, 'You are not authorized to view information about this tournament!')
        return HttpResponseRedirect('/failure.html/')

    if request.method == 'POST' and (user == qset.owner or user in qset_editors):

        form = QuestionSetForm(data=request.POST)
        if form.is_valid():
            qset = QuestionSet.objects.get(id=qset_id)
            qset.name = form.cleaned_data['name']
            qset.date = form.cleaned_data['date']
            qset.distribution = form.cleaned_data['distribution']
            qset.num_packets = form.cleaned_data['num_packets']
            qset.save()

            if user == qset.owner:
                tossups = Tossup.objects.filter(question_set=qset)
                bonuses = Bonus.objects.filter(question_set=qset)
                set_distro_formset = create_set_distro_formset(qset)
                tiebreak_formset = create_tiebreak_formset(qset)
            else:
                read_only = True

            entries = qset.setwidedistributionentry_set.all()
            for entry in entries:
                tu_required = entry.num_tossups
                bs_required = entry.num_bonuses
                tu_written = qset.tossup_set.filter(category=entry.dist_entry).count()
                bs_written = qset.bonus_set.filter(category=entry.dist_entry).count()
                total_tu_req += tu_required
                total_bs_req += bs_required
                total_bs_written += bs_written
                total_tu_written += tu_written

                set_status[str(entry.dist_entry)] = {'tu_req': tu_required,
                                                     'tu_in_cat': tu_written,
                                                     'bs_req': bs_required,
                                                     'bs_in_cat': bs_written}
            set_pct_complete = float(total_tu_written + total_bs_written) / float(total_tu_req + total_bs_req)

            return render_to_response('edit_question_set.html',
                                      {'form': form,
                                       'qset': qset,
                                       'user': user,
                                       'editors': [ed for ed in qset_editors if ed != qset.owner],
                                       'writers': qset.writer.all(),
                                       'set_distro_formset': set_distro_formset,
                                       'tiebreak_formset': tiebreak_formset,
                                       'upload_form': QuestionUploadForm(),
                                       'set_status': set_status,
                                       'set_pct_complete': '{0:0.2f}%'.format(set_pct_complete),
                                       'tu_needed': total_tu_req - total_tu_written,
                                       'bs_needed': total_bs_req - total_bs_written,
                                       'tossups': tossups,
                                       'bonuses': bonuses,
                                       'packets': qset.packet_set.all(),
                                       'message': 'Your changes have been successfully saved.',
                                       'message_class': 'alert-success'},
                                      context_instance=RequestContext(request))
        else:
            qset_editors = []
    else:
        if user not in qset_editors and user != qset.owner:
            form = QuestionSetForm(instance=qset, read_only=True)
            read_only = True
            message = 'You are not authorized to edit this tournament.'
            if user in qset.writer.all():
                tossups = Tossup.objects.filter(question_set=qset)
                bonuses = Bonus.objects.filter(question_set=qset)
                set_distro_formset = create_set_distro_formset(qset)
                tiebreak_formset = create_tiebreak_formset(qset)
        else:
            if user == qset.owner:
                read_only = False
                tossups = Tossup.objects.filter(question_set=qset)
                bonuses = Bonus.objects.filter(question_set=qset)
                set_distro_formset = create_set_distro_formset(qset)
                tiebreak_formset = create_tiebreak_formset(qset)
            elif user in qset.writer.all() or user in qset.editor.all():
                read_only = True
                tossups = Tossup.objects.filter(question_set=qset)
                bonuses = Bonus.objects.filter(question_set=qset)
                set_distro_formset = create_set_distro_formset(qset)
                tiebreak_formset = create_tiebreak_formset(qset)
            form = QuestionSetForm(instance=qset)

        entries = qset.setwidedistributionentry_set.all()
        for entry in entries:
            tu_required = entry.num_tossups
            bs_required = entry.num_bonuses
            tu_written = qset.tossup_set.filter(category=entry.dist_entry).count()
            bs_written = qset.bonus_set.filter(category=entry.dist_entry).count()
            total_tu_req += tu_required
            total_bs_req += bs_required
            total_bs_written += bs_written
            total_tu_written += tu_written
            set_status[str(entry.dist_entry)] = {'tu_req': tu_required,
                                                     'tu_in_cat': tu_written,
                                                     'bs_req': bs_required,
                                                     'bs_in_cat': bs_written}
        set_pct_complete = float(total_tu_written + total_bs_written) / float(total_tu_req + total_bs_req)

    print tiebreak_formset
        
    return render_to_response('edit_question_set.html',
                              {'form': form,
                               'user': user,
                               'editors': [ed for ed in qset_editors if ed != qset.owner],
                               'writers': [wr for wr in qset_writers if wr != qset.owner],
                               'set_distro_formset': set_distro_formset,
                               'tiebreak_formset': tiebreak_formset,
                               'set_status': set_status,
                               'set_pct_complete': '{0:0.2f}%'.format(set_pct_complete),
                               'tu_needed': total_tu_req - total_tu_written,
                               'bs_needed': total_bs_req - total_bs_written,
                               'upload_form': QuestionUploadForm(),
                               'tossups': tossups,
                               'bonuses': bonuses,
                               'packets': qset.packet_set.all(),
                               'qset': qset,
                               'read_only': read_only,
                               'message': message},
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

            return HttpResponseRedirect('/edit_question_set/{0}'.format(qset_id))
        else:
            print formset

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

            return HttpResponseRedirect('/edit_question_set/{0}'.format(qset_id))
        else:
            print formset


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
            available_editors = [writer for writer in Writer.objects.all()
                                 if writer not in current_editors and writer != qset.owner and writer.id != 1]
            print available_editors
        else:
            available_editors = []
            message = 'You are not authorized to make changes to this tournament!'
        return render_to_response('add_editor.html',
                                 {'qset': qset,
                                  'available_editors': available_editors,
                                  'message': message,
                                  'user': user},
                                  context_instance=RequestContext(request))


    elif request.method == 'POST':
        print request.POST
        if user == qset.owner:
            editors_to_add = request.POST.getlist('editors_to_add')
            # do some basic validation here
            if all([x.isdigit() for x in editors_to_add]):
                for editor_id in editors_to_add:
                    print editor_id
                    editor = Writer.objects.get(id=editor_id)
                    qset.editor.add(editor)
                qset.save()
                current_editors = qset.editor.all()
                available_editors = [writer for writer in Writer.objects.all()
                                     if writer not in current_editors and writer != qset.owner and writer.id != 1]
            else:
                message = 'Invalid data entered!'
                available_editors = []
        else:
            available_editors = []
            message = 'You are not authorized to make changes to this tournament!'

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

    if request.method == 'GET':
        if user == qset.owner:
            current_writers = qset.writer.all()
            current_editors = qset.editor.all()
            available_writers = [writer for writer in Writer.objects.all()
                                 if writer not in current_writers
                                 and writer not in current_editors
                                 and writer != qset.owner and writer.id != 1]
            print available_writers
        else:
            available_writers = []
            message = 'You are not authorized to make changes to this tournament!'
        return render_to_response('add_writer.html',
                                 {'qset': qset,
                                  'available_writers': available_writers,
                                  'message': message,
                                  'user': user},
                                  context_instance=RequestContext(request))


    elif request.method == 'POST':
        print request.POST
        if user == qset.owner:
            writers_to_add = request.POST.getlist('writers_to_add')
            # do some basic validation here
            if all([x.isdigit() for x in writers_to_add]):
                for writer_id in writers_to_add:
                    print writer_id
                    writer = Writer.objects.get(id=writer_id)
                    qset.writer.add(writer)
                qset.save()
                current_writers = qset.writer.all()
                current_editors = qset.editor.all()
                available_writers = [writer for writer in Writer.objects.all()
                                     if writer not in current_writers
                                     and writer not in current_editors
                                     and writer != qset.owner and writer.id != 1]
            else:
                message = 'Invalid data entered!'
                available_writers = []
        else:
            available_writers = []
            message = 'You are not authorized to make changes to this tournament!'

        return render_to_response('add_writer.html',
            {'qset': qset,
             'available_editors': available_writers,
             'message': message,
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
            message_class = 'alert alert-danger'
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


def edit_tossups(request, packet_id):
    pass

def edit_bonuses(request, packet_id):
    pass

@login_required
def add_tossups(request, qset_id, packet_id=None):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    message = ''
    message_class = ''
    tossup = None
    read_only = True

    if request.method == 'GET':
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            if user in qset.writer.all() and user not in qset.editor.all() and user != qset.owner:
                tossup_form = TossupForm(qset_id=qset.id, packet_id=packet_id, role='writer')
            else:
                tossup_form = TossupForm(qset_id=qset.id, packet_id=packet_id)
            #dist = qset.distribution
            #dist_entries = dist.distributionentry_set.all()
            #tossup_form.fields['category'].queryset = dist_entries
            read_only = False
        else:
            tossup_form = None
            message = 'You are not authorized to add questions to this tournament!'
            message_class = 'alert alert-warning'
            read_only = True

        return render_to_response('add_tossups.html',
            {'form': tossup_form,
             'message': message,
             'message_class': message_class,
             'read_only': read_only,
             'user': user},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            # The user may have set the packet ID through the POST body, so check for it there
            if packet_id == None and 'packet' in request.POST and request.POST['packet'] != '':
                packet_id = int(request.POST['packet'])
            tossup_form = TossupForm(request.POST, qset_id=qset.id, packet_id=packet_id)

            if tossup_form.is_valid():
                tossup = tossup_form.save(commit=False)
                tossup.author = user
                tossup.question_set = qset
                tossup.tossup_text = sanitize_html(tossup.tossup_text)
                tossup.tossup_answer = sanitize_html(tossup.tossup_answer)
                # New questions should not be auto-locked. Also, the user has no way to currently change this setting.
                tossup.locked = False
                if packet_id is None or packet_id == '':
                    tossup.question_number = -1 # Tossups have no order until they are assigned to a packet
                else:
                    tossup.question_number = Tossup.objects.filter(packet_id=packet_id).count()
                tossup.save()
                message = 'Your tossup has been successfully added to the set! Write more questions!'
                message_class = 'alert alert-success'

            else:
                for field in tossup_form:
                    print field
                    print field.errors

            read_only = False
        else:
            tossup = None
            message = 'You are not authorized to add questions to this tournament!'
            message_class = 'alert alert-warning'
            tossup_form = []
            read_only = True

        return render_to_response('add_tossups.html',
                 {'form': TossupForm(qset_id=qset.id, packet_id=packet_id),
                 'message': message,
                 'message_class': message_class,
                 'tossup': tossup,
                 'read_only': read_only,
                 'user': user},
                 context_instance=RequestContext(request))

    else:
        return render_to_response('failure.html',
            {'message': 'The request cannot be completed as specified',
             'message-class': 'alert alert-error'},
            context_instance=RequestContext(request))

@login_required
def add_bonuses(request, qset_id, packet_id=None):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    message = ''
    message_class = ''
    read_only = True
    role = get_role(user, qset)

    if request.method == 'GET':
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            form = BonusForm(qset_id=qset.id, packet_id=packet_id, role=role)
            read_only = False
        else:
            form = None
            message = 'You are not authorized to add questions to this tournament!'
            message_class = 'alert alert-warning'
            read_only = True

        return render_to_response('add_bonuses.html',
            {'form': form,
             'message': message,
             'message_class': message_class,
             'read_only': read_only,
             'user': user},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            form = BonusForm(request.POST, qset_id=qset.id, packet_id=packet_id)

            if form.is_valid():
                bonus = form.save(commit=False)
                bonus.author = user
                bonus.question_set = qset
                bonus.leadin = sanitize_html(bonus.leadin)
                bonus.part1_text = sanitize_html(bonus.part1_text)
                bonus.part1_answer = sanitize_html(bonus.part1_answer)
                bonus.part2_text = sanitize_html(bonus.part2_text)
                bonus.part2_answer = sanitize_html(bonus.part2_answer)
                bonus.part3_text = sanitize_html(bonus.part3_text)
                bonus.part3_answer = sanitize_html(bonus.part3_answer)
                # New questions should not be auto-locked. Also, the user has no way to currently change this setting.
                bonus.locked = False
                if packet_id is None or packet_id == '':
                    bonus.question_number = -1 # Bonuses have no order until they are assigned to a packet
                else:
                    bonus.packet_id = packet_id
                    bonus.question_number = Bonus.objects.filter(packet_id=packet_id).count()
                bonus.save()
                message = 'Your bonus has been successfully added to the set! Write more questions!'
                message_class = 'alert alert-success'

            else:
                for field in form:
                    print field
                    print field.errors

            read_only = False
        else:
            message = 'You are not authorized to add questions to this tournament!'
            message_class = 'alert alert-warning'
            bonus_form = []
            bonus = None
            read_only = True

        return render_to_response('add_bonuses.html',
                 {'form': BonusForm(qset_id=qset.id, packet_id=packet_id),
                 'message': message,
                 'message_class': message_class,
                 'bonus': bonus,
                 'read_only': read_only,
                 'user': user},
                 context_instance=RequestContext(request))

    else:
        return render_to_response('failure.html',
            {'message': 'The request cannot be completed as specified',
             'message-class': 'alert alert-error'},
            context_instance=RequestContext(request))

@login_required
def edit_tossup(request, tossup_id):
    user = request.user.writer
    tossup = Tossup.objects.get(id=tossup_id)
    qset = tossup.question_set
    packet = tossup.packet
    message = ''
    message_class = ''
    read_only = True
    role = get_role(user, qset)

    if request.method == 'GET':
        if user == tossup.author or user == qset.owner or user in qset.editor.all():
            form = TossupForm(instance=tossup, qset_id=qset.id, role=role)
            if user == tossup.author and not user == qset.owner and not user in qset.editor.all() and tossup.locked:
                read_only = True
                message = 'This tossup has been locked by an editor. It cannot be changed except by another editor.'
                message_class = 'alert alert-warning'
            else:
                read_only = False

        elif user in qset.writer.all():
            read_only = True
            form = None
            message = 'You are only authorized to view, not to edit, this question!'
            message_class = 'alert alert-warning'
        else:
            read_only = True
            tossup = None
            form = None
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert alert-danger'

        return render_to_response('edit_tossup.html',
            {'tossup': tossup,
             'form': form,
             'qset': qset,
             'packet': packet,
             'message': message,
             'message_class': message_class,
             'read_only': read_only,
             'user': user},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        if user == tossup.author or user == qset.owner or user in qset.editor.all():

            form = TossupForm(request.POST, qset_id=qset.id, role=role)
            can_change = True
            if user == tossup.author and tossup.locked:
                can_change = False

            if form.is_valid() and can_change:
                #print form.cleaned_data['tossup_text']
                print form.cleaned_data['tossup_answer']

                tossup.tossup_text = sanitize_html(form.cleaned_data['tossup_text'])
                tossup.tossup_answer = sanitize_html(form.cleaned_data['tossup_answer'])

                #print tossup.tossup_text
                print tossup.tossup_answer

                tossup.category = form.cleaned_data['category']
                tossup.packet = form.cleaned_data['packet']
                tossup.locked = form.cleaned_data['locked']
                tossup.edited = form.cleaned_data['edited']
                tossup.question_type = form.cleaned_data['question_type']
                tossup.save()
                message = 'Your changes have been saved!'
                message_class = 'alert alert-success'

                read_only = False
            elif form.is_valid() and not can_change:
                message = 'This tossup is locked and can only be changed by an editor!'
                message_class = 'alert alert-warning'
                read_only = True

        elif user in qset.writer.all():
            read_only = True
            form = None
            message = 'You are only authorized to view, not to edit, this question!'
            message_class = 'alert alert-warning'
        else:
            read_only = True
            tossup = None
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert alert-error'

        return render_to_response('edit_tossup.html',
            {'tossup': tossup,
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
    qset = bonus.question_set
    packet = bonus.packet
    message = ''
    message_class = ''
    read_only = True
    role = get_role(user, qset)

    if request.method == 'GET':
        if user == bonus.author or user == qset.owner or user in qset.editor.all():
            form = BonusForm(instance=bonus, qset_id=qset.id, role=role)
            if user == bonus.author and not user == qset.owner and not user in qset.editor.all() and bonus.locked:
                read_only = True
                message = 'This bonus has been locked by an editor. It cannot be changed except by another editor.'
                message_class = 'alert alert-warning'
            else:
                read_only = False

        elif user in qset.writer.all():
            read_only = True
            form = None
            message = 'You are only authorized to view, not to edit, this question!'
            message_class = 'alert alert-warning'
        else:
            read_only = True
            bonus = None
            form = None
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert alert-danger'

        return render_to_response('edit_bonus.html',
            {'bonus': bonus,
             'form': form,
             'qset': qset,
             'packet': packet,
             'message': message,
             'message_class': message_class,
             'read_only': read_only,
             'user': user},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        if user == bonus.author or user == qset.owner or user in qset.editor.all():
            form = BonusForm(request.POST, qset_id=qset.id, role=role)
            can_change = True
            if user == bonus.author and bonus.locked:
                can_change = False

            if form.is_valid() and can_change:
                bonus.leadin = sanitize_html(form.cleaned_data['leadin'])
                bonus.part1_text = sanitize_html(form.cleaned_data['part1_text'])
                bonus.part1_answer = sanitize_html(form.cleaned_data['part1_answer'])
                bonus.part2_text = sanitize_html(form.cleaned_data['part2_text'])
                bonus.part2_answer = sanitize_html(form.cleaned_data['part2_answer'])
                bonus.part3_text = sanitize_html(form.cleaned_data['part3_text'])
                bonus.part3_answer = sanitize_html(form.cleaned_data['part3_answer'])
                bonus.category = form.cleaned_data['category']
                bonus.packet = form.cleaned_data['packet']
                bonus.locked = form.cleaned_data['locked']
                bonus.edited = form.cleaned_data['edited']
                bonus.question_type = form.cleaned_data['question_type']
                bonus.save()

                #print bonus.part1_text

                message = 'Your changes have been saved!'
                message_class = 'alert alert-success'
                read_only = False

            elif form.is_valid() and not can_change:
                message = 'This bonus is locked and can only be changed by an editor!'
                message_class = 'alert alert-warning'
                read_only = True

        elif user in qset.writer.all():
            form = None
            read_only = True
            message = 'You are only authorized to view, not to edit, this question!'
            message_class = 'alert alert-warning'
        else:
            form = None
            bonus = None
            read_only = True
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert alert-danger'

        return render_to_response('edit_bonus.html',
            {'bonus': bonus,
             'form': form,
             'qset': qset,
             'packet': packet,
             'message': message,
             'message_class': message_class,
             'read_only': read_only,
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
            message_class = 'alert alert-success'
            read_only = False
        else:
            message = 'You are not authorized to delete questions from this set!'
            message_class = 'alert alert-warning'

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
            message = 'Bonus deleted'
            message_class = 'alert alert-success'
            read_only = False
        else:
            message = 'You are not authorized to delete questions from this set!'
            message_class = 'alert alert-warning'

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
                if packet_name is not None and (name_base is None or num_packets is None):
                    new_packet = Packet()
                    new_packet.packet_name = packet_name
                    new_packet.created_by = user
                    new_packet.question_set = qset
                    new_packet.save()
                    message = 'Your packet named {0} has been created!'.format(name_base)
                    message_class = 'alert alert-success'

                elif name_base is not None and num_packets is not None:
                    for i in range(1, num_packets + 1):
                        new_packet = Packet()
                        new_packet.packet_name = '{0!s} {1:02}'.format(name_base, i)
                        new_packet.created_by = user
                        new_packet.question_set = qset
                        new_packet.save()
                    message = 'Your {0} packets with the base name {1} have been created!'.format(num_packets, name_base)
                    message_class = 'alert alert-success'
                else:
                    message = 'You must enter either the name for an individual packet or a base name and the number of packets to create!'
                    message_class = 'alert alert-warning'

            else:
                message = 'Invalid information entered into form!'
                message_class = 'alert alert-danger'
        else:
            message = 'Invalid method!'
            message_class = 'alert alert-danger'
            form = None

    else:
        message = 'You are not authorized to add packets to this set!'
        message_class = 'alert alert-danger'
        form = None

    return render_to_response('add_packets.html',
        {'message': message,
         'message_class': message_class,
         'form': form,
         'user': user},
        context_instance=RequestContext(request))

@login_required
def delete_packet(request):
    user = request.user.writer

    message = ''
    message_class = ''
    read_only = True

    if request.method == 'POST':
        packet_id = request.POST['packet_id']
        packet = Packet.objects.get(id=packet_id)
        qset = packet.question_set
        if user == qset.owner:
            #packet.delete()
            message = 'Packet deleted'
            message_class = 'alert alert-success'
            read_only = False
        else:
            message = 'You are not authorized to delete packets from this set!'
            message_class = 'alert alert-warning'

    return HttpResponse(json.dumps({'message': message, 'message_class': message_class}))

@login_required
def get_unassigned_tossups(request):
    user = request.user.writer
    qset_id = request.GET['qset_id']
    message = ''
    message_class = ''
    data = []

    print request.GET['qset_id']

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
                message_class = 'alert alert-danger'

        else:
            message = 'Invalid request!'
            message_class = 'alert alert-danger'
    except Exception as ex:
        print ex
        message = 'Unable to retrieve question set; qset_id either missing or incorrect!'
        message_class = 'alert alert-danger'

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
                message_class = 'alert alert-danger'

        else:
            message = 'Invalid request!'
            message_class = 'alert alert-danger'
    except Exception as ex:
        print ex
        message = 'Unable to retrieve question set; qset_id either missing or incorrect!'
        message_class = 'alert alert-danger'

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
                message_class = 'alert alert-success'
                tossup.save()
        else:
            message = 'Only the set owner is authorized to add questions to the set!'
            message_class = 'alert alert-warning'

    else:
        message = 'Invalid request!'
        message_class = 'alert alert-danger'

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
                message_class = 'alert alert-success'
                bonus.save()
        else:
            message = 'Only the set owner is authorized to add questions to the set!'
            message_class = 'alert alert-warning'

    else:
        message = 'Invalid request!'
        message_class = 'alert alert-danger'

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
                message = ''
                message_class = ''

            except Exception as ex:
                print ex
                message = 'Something went terribly wrong!'
                message_class = 'alert alert-danger'

        else:
            message = 'Only the owner of the set is allowed to change the order of questions!'
            message_class = 'alert alert-warning'
    else:
        message = 'Invalid request!'
        message_class = 'alert alert-warning'

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
#             message_class = 'alert alert-warning'
#     else:
#         message = 'Invalid request!'
#         message_class = 'alert alert-danger'
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
#             message_class = 'alert alert-warning'
#     else:
#         message = 'Invalid request!'
#         message_class = 'alert alert-danger'
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

def add_question(request, type, packet_id):
    
    # need some role checking here to make sure user is authorized to do this
    # also allowed categories have to be restricted
    
    if request.user.is_authenticated():
        player = request.user.get_profile()
        packet = Packet.objects.get(id=packet_id)
        team = packet.team
        
        if player not in packet.authors.all():
            return render_to_response('failure.html',
                                      {'message': 'You are not authorized to edit this packet!'})
        
        
        if request.method == 'POST':
            if type == 'tossup':
                form = TossupForm(request.POST)
            elif type == 'bonus':
                form = BonusForm(request.POST)
            else:
                return render_to_response('failure.html',
                                          {'message': 'Unknown question type specified!',
                                           'message_type': 'error'})   
            if form.is_valid():
                question = form.save(commit=False)
                     
                if player.teamrole_set.filter(team_id=team.id).exists():
                    player_role = player.teamrole_set.get(team_id=team.id)
                    allowed_categories = player_role.category.split(';')
                    selected_category = form.cleaned_data['category']
                else:
                    player_role = None
                    allowed_categories = []
                    selected_category = []

                print allowed_categories, selected_category

                if selected_category not in allowed_categories:
                    return render_to_response('addquestion.html',
                                              {'form': form,
                                               'message': 'You cannot add questions of this category type. ' \
                                               'If you want to add questions from this category, ask the team manager to assign it to you. ' \
                                               'Your input has NOT been saved!',
                                               'message_type': 'error'},
                                              context_instance=RequestContext(request))
                question.author = player
                question.packet = packet
                question.save()
                
                return HttpResponseRedirect('/editquestion/' + type + '/' + str(question.id))
            else:
                return render_to_response('addquestion.html',
                                          {'form': form,
                                           'packet': packet},
                                          context_instance=RequestContext(request))
        else:
            if type == 'tossup':
                form = TossupForm()
            elif type == 'bonus':
                form = BonusForm()
            else:
                return render_to_response('failure.html',
                                          {'message': 'Unknown question type specified!',
                                           'message_type': 'error'})

            return render_to_response('addquestion.html',
                                      {'form': form,
                                       'packet': packet},
                                      context_instance=RequestContext(request))
        
    else:
        return HttpResponseRedirect('/accounts/login/')
    
def edit_question(request, type, question_id):
    
    if type != 'tossup' and type != 'bonus':
        return render_to_response('failure.html',
                                  {'message': 'Not a valid question type!',
                                   'message_type': 'error'})
    
    if request.user.is_authenticated():
        player = request.user.get_profile()
        if type == 'tossup':
            question = Tossup.objects.get(id=question_id)
        elif type == 'bonus':
            question = Bonus.objects.get(id=question_id)
            
        packet = question.packet
        team = packet.team
        
        if request.method == 'POST':
            if type == 'tossup':
                form = TossupForm(request.POST)
            elif type == 'bonus':
                form = BonusForm(request.POST)
                
            if form.is_valid():
                
                if player.teamrole_set.filter(team_id=team.id).exists():
                    player_role = player.teamrole_set.get(team_id=team.id)
                    allowed_categories = player_role.category.split(';')
                    selected_category = form.cleaned_data['category']
                else:
                    player_role = None
                    allowed_categories = []
                    selected_category = []

                print allowed_categories, selected_category

                if selected_category not in allowed_categories:
                    return render_to_response('editquestion.html',
                                              {'form': form,
                                               'message': 'You cannot edit questions of this category type. ' \
                                               'If you want to edit questions from this category, ask the team manager to assign it to you. ' \
                                               'Your input has NOT been saved!',
                                               'message_type': 'error'},
                                              context_instance=RequestContext(request))
                

                if type == 'tossup':
                    question.tossup_text = form.cleaned_data['tossup_text']
                    question.tossup_answer = form.cleaned_data['tossup_answer']
                    
                elif type == 'bonus':
                    question.leadin = form.cleaned_data['leadin']
                    question.part1_text = form.cleaned_data['part1_text']
                    question.part2_text = form.cleaned_data['part2_text']
                    question.part3_text = form.cleaned_data['part3_text']
                    question.part1_answer = form.cleaned_data['part1_answer']
                    question.part2_answer = form.cleaned_data['part2_answer']
                    question.part3_answer = form.cleaned_data['part3_answer']
                
                question.category = form.cleaned_data['category']
                question.subtype = form.cleaned_data['subtype']
                question.location = form.cleaned_data['location']
                question.time_period = form.cleaned_data['time_period']
                question.save()
                
            return render_to_response('editquestion.html',
                                      {'form': form,
                                       'packet': packet},
                                       context_instance=RequestContext(request))
        else:
            if type == 'tossup':
                form = TossupForm(instance=question)
            elif type == 'bonus':
                form = BonusForm(instance=question)
            
        return render_to_response('editquestion.html',
                                  {'form': form,
                                   'packet': packet},
                                  context_instance=RequestContext(request))
        
    else:
        return HttpResponseRedirect('/accounts/login/')
            
            
def add_bonus(request, packet_id):
    pass


@login_required
def distributions (request):
    
    data = []
    all_dists = Distribution.objects.all()
        
    return render_to_response('distributions.html',
                              {'dists': all_dists, 'user': request.user.writer},
                              context_instance=RequestContext(request))

def edit_distribution(request, dist_id=None):
    
    data = []

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
                            new_entry.distribution = new_dist
                            new_entry.save()

                    return HttpResponseRedirect('/edit_distribution/' + str(new_dist.id))
                        
            else:
                formset = DistributionEntryFormset(data=request.POST, prefix='distentry')
                dist_form = DistributionForm(data=request.POST)
                print dist_form.is_valid()
                print formset.is_valid()
                print formset.errors
                if dist_form.is_valid() and formset.is_valid():
                    
                    dist = Distribution.objects.get(id=dist_id)
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
                                    entry.min_bonuses = form.cleaned_data['min_bonuses']
                                    entry.min_tossups = form.cleaned_data['min_tossups']
                                    entry.max_bonuses = form.cleaned_data['max_bonuses']
                                    entry.max_tossups = form.cleaned_data['max_tossups']
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
                                        print 'here'
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
                                       'formset': formset},
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
                                       'formset': formset,},
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

    print request.GET
    print request.POST
    user = request.user.writer
    qset_id = request.POST['qset-id']
    qset = QuestionSet.objects.get(id=qset_id)

    if request.method == 'POST':
        comment_text = request.POST['comment-text']
        print comment_text


@login_required
def upload_questions(request, qset_id):
    qset = QuestionSet.objects.get(id=qset_id)
    user = request.user.writer

    if request.method == 'POST':
        if (user == qset.owner or user in qset.editor.all() or user in qset.writer.all()):
            form = QuestionUploadForm(request.POST, request.FILES)
            print form
            if form.is_valid():
                uploaded_tossups, uploaded_bonuses = handle_uploaded_packet(request.FILES['questions_file'])

                return render_to_response('upload_preview.html',
                {'tossups': uploaded_tossups,
                'bonuses': uploaded_bonuses,
                'message': mark_safe('Please verify that this data is correct. Hitting "Submit" will upload these questions '\
                'If you see any mistakes in the submissions, please correct them in the <strong><em>original file</em></strong> and reupload.'),
                'message_class': 'alert alert-warning',
                'qset': qset},
                context_instance=RequestContext(request))
            else:
                messages.error(request, form.questions_file.errors)
                return HttpResponseRedirect('/edit_question_set/{0}'.format(qset_id))
        else:
            messages.error(request, 'You do not have permission to upload ')

@login_required
def complete_upload(request):
    user = request.user.writer

    if request.method == 'POST':
        qset_id = request.POST['qset-id']
        qset = QuestionSet.objects.get(id=qset_id)

        num_tossups = int(request.POST['num-tossups'])
        num_bonuses = int(request.POST['num-bonuses'])

        for tu_num in range(num_tossups):
            tu_text_name = 'tossup-text-{0}'.format(tu_num)
            tu_ans_name = 'tossup-answer-{0}'.format(tu_num)

            tu_text = request.POST[tu_text_name]
            tu_ans = request.POST[tu_ans_name]

            new_tossup = Tossup()
            new_tossup.tossup_text = tu_text
            new_tossup.tossup_answer = tu_ans
            new_tossup.author = user
            new_tossup.question_set = qset
            new_tossup.edited = False

            new_tossup.save()

        for bs_num in range(num_bonuses):
            bs_leadin_name = 'bonus-leadin-{0}'.format(bs_num)

            bs_part1_name = 'bonus-part1-{0}'.format(bs_num)
            bs_ans1_name = 'bonus-answer1-{0}'.format(bs_num)
            bs_part2_name = 'bonus-part2-{0}'.format(bs_num)
            bs_ans2_name = 'bonus-answer2-{0}'.format(bs_num)
            bs_part3_name = 'bonus-part3-{0}'.format(bs_num)
            bs_ans3_name = 'bonus-answer3-{0}'.format(bs_num)

            new_bonus = Bonus()
            new_bonus.question_set = qset
            new_bonus.author = user
            new_bonus.edited = False
            new_bonus.leadin = request.POST[bs_leadin_name]
            new_bonus.part1_text = request.POST[bs_part1_name]
            new_bonus.part1_answer = request.POST[bs_ans1_name]
            new_bonus.part2_text = request.POST[bs_part2_name]
            new_bonus.part2_answer = request.POST[bs_ans2_name]
            new_bonus.part3_text = request.POST[bs_part3_name]
            new_bonus.part3_answer = request.POST[bs_ans3_name]

            new_bonus.save()

        messages.success(request, 'Your questions have been uploaded!')
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

    if request.method == 'GET':
        initial_data = {'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'email': user.email}

        form = WriterChangeForm(initial=initial_data)

    elif request.method == 'POST':

        print request.POST
        form = WriterChangeForm(request.POST)

        if form.is_valid():
            print 'valid'
            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.email = form.cleaned_data['email']
            user.save()

    return render_to_response('profile.html',
            {'form': form,
             'user': user},
            context_instance=RequestContext(request))

# @login_required
# def password(request):
#
#     user = request.user
#
#     if request.method == 'GET':
#         form = PasswordChangeForm(user)
#
#         return render_to_response('password.html',
#             {'form': form,
#              'user': user},
#             context_instance=RequestContext(request))
#
#     elif request.method == 'POST':
#         pass
