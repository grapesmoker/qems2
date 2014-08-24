import json

from django.template.loader import get_template
from django.template import Context, RequestContext
from django.shortcuts import render_to_response
from django import forms
from django.forms.formsets import formset_factory
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from models import *
from forms import *
from utils import *

from collections import OrderedDict
from itertools import chain


def register (request):
    if request.method == 'POST':
        form = WriterCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            print form.cleaned_data
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
    print request.user.is_authenticated()
    return render_to_response('main.html', {'user': request.user},
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
    return render_to_response('question_sets.html', {'question_set_list': all_sets},
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
    if request.method == 'POST':
        form = QuestionSetForm(data=request.POST)
        if form.is_valid():
            writer = request.user.writer
            # for the moment, just use the default ACF Distribution
            dist = Distribution.objects.get(id=1)
            question_set = form.save(commit=False)
            question_set.owner = writer
            question_set.distribution = dist
            question_set.save()
            form.save_m2m()
            writer.question_set_editor.add(question_set)
            writer.save()
            
            return render_to_response('success.html',
                                      {'message': 'Your question set has been successfully created!'},
                                      context_instance=RequestContext(request))
        else:
            print form.errors
            return render_to_response('failure.html',
                                      {'message': 'There was an error in creating your question set!'},
                                      context_instance=RequestContext(request))
    else:
        form = QuestionSetForm()
        
    return render_to_response('create_question_set.html',
                              {'form': form},
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

    if request.method == 'POST' and (user == qset.owner or user in qset_editors):
        print request.POST
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
            
            return render_to_response('edit_question_set.html',
                                      {'form': form,
                                       'qset': qset,
                                       'editors': [ed for ed in qset_editors if ed != qset.owner],
                                       'writers': qset.writer.all(),
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
        else:
            if user == qset.owner:
                tossups = Tossup.objects.filter(question_set=qset)
                bonuses = Bonus.objects.filter(question_set=qset)
            form = QuestionSetForm(instance=qset)
        
        
    return render_to_response('edit_question_set.html',
                              {'form': form,
                               'editors': [ed for ed in qset_editors if ed != qset.owner],
                               'writers': [wr for wr in qset_writers if wr != qset.owner],
                               'tossups': tossups,
                               'bonuses': bonuses,
                               'packets': qset.packet_set.all(),
                               'qset': qset,
                               'read_only': read_only,
                               'message': message},
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
            available_editors = [writer for writer in Writer.objects.all()
                                 if writer not in current_editors and writer != qset.owner and writer.id != 1]
            print available_editors
        else:
            available_editors = []
            message = 'You are not authorized to make changes to this tournament!'
        return render_to_response('add_editor.html',
                                 {'qset': qset,
                                  'available_editors': available_editors,
                                  'message': message},
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
             'message': message},
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
                                  'message': message},
                                  context_instance=RequestContext(request))


    elif request.method == 'POST':
        print request.POST
        if user == qset.owner:
            writers_to_add = request.POST.getlist('writers_to_add')
            # do some basic validation here
            if all([x.isdigit() for x in writers_to_add]):
                for writer_id in writers_to_add:
                    print writer_id
                    editor = Writer.objects.get(id=writer_id)
                    qset.editor.add(editor)
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
             'message': message},
            context_instance=RequestContext(request))

def edit_packet(request, packet_id):
    
    print "editing ", packet_id
    
    if request.user.is_authenticated():
        player = request.user.get_profile()
        packet = Packet.objects.get(id=packet_id)
        team = packet.team
        teammates = team.player_set.all()
        
        all_teammates = chain([player], teammates)
        
        tossups = packet.tossup_set.all()
        bonuses = packet.bonus_set.all()
        
        tu_cat_table = {}
        b_cat_table = {}
        cat_names = {'S': 'Science',
                     'L': 'Literature',
                     'H': 'History',
                     'R': 'Religion',
                     'M': 'Myth',
                     'P': 'Philosophy',
                     'FA': 'Fine Arts',
                     'SS': 'Social Science',
                     'G': 'Geography',
                     'PC': 'Pop culture/Current events'}
        
        # right now the ACF distro is hard-coded in
        
        for cat in ACF_DISTRO:
            tu_cat_table.setdefault(cat, 0)
            b_cat_table.setdefault(cat, 0)
            
        for tossup in tossups:
            cat = tossup.category.split('-')[0]
            if cat in ACF_DISTRO:
                tu_cat_table[cat] += 1
                
        for bonus in bonuses:
            cat = bonus.category.split('-')[0]
            if cat in ACF_DISTRO:
                b_cat_table[cat] += 1
        
        teammate_questions = []
        
        class TeammateQInfo:
            name = ''
            tu_cat_table = {}
            b_cat_table = {}
            
            def __init__(self):
                for cat in ACF_DISTRO:
                    self.tu_cat_table.setdefault(cat, 0)
                    self.b_cat_table.setdefault(cat, 0)
        
        for teammate in all_teammates:
            tq = TeammateQInfo()
            tq.name = teammate.user.username
            
            tm_tus = teammate.tossup_set.filter(packet=packet)
            tm_bns = teammate.bonus_set.filter(packet=packet)
            
            print tq.name, len(tm_tus), len(tm_bns)
            for tm_tu in tm_tus:
                cat = tm_tu.category.split('-')[0]
                if cat in ACF_DISTRO:
                    tq.tu_cat_table[cat] += 1
            for tm_bn in tm_bns:
                cat = tm_tu.category.split('-')[0]
                if cat in ACF_DISTRO:
                    tq.b_cat_table[cat] += 1
                    
            print tq.tu_cat_table
            teammate_questions.append(tq)
        
        
        return render_to_response('packetedit.html',
                                  {'player': player,
                                   'tu_cat_table': tu_cat_table,
                                   'b_cat_table': b_cat_table,
                                   'categories': ACF_DISTRO.keys(),
                                   'distribution': ACF_DISTRO,
                                   'cat_names': cat_names,
                                   'packet': packet,
                                   'teammate_questions': teammate_questions},
                                  context_instance=RequestContext(request))
        
    else:
        return HttpResponseRedirect('/accounts/login/')


def edit_tossups(request, packet_id):
    pass

def edit_bonuses(request, packet_id):
    pass

@login_required
def add_tossups(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'GET':
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            tossup_form = TossupForm(qset_id=qset.id)
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
             'read_only': read_only},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            tossup_form = TossupForm(request.POST, qset_id=qset.id)
            #dist = qset.distribution
            #dist_entries = dist.distributionentry_set.all()
            #tossup_form.fields['category'].queryset = dist_entries
            #tossup_form.data = request.POST.copy()
            #tossup_form.is_bound = True

            if tossup_form.is_valid():
                tossup = tossup_form.save(commit=False)
                tossup.author = user
                tossup.question_set = qset
                tossup.save()
                message = 'Your tossup has been successfully added to the set! Write more questions!'
                message_class = 'alert alert-success'
            else:
                print request.POST
            read_only = False
        else:
            message = 'You are not authorized to add questions to this tournament!'
            message_class = 'alert alert-warning'
            tossup_form = []
            read_only = True

        return render_to_response('add_tossups.html',
                 {'form': TossupForm(qset_id=qset.id),
                 'message': message,
                 'message_class': message_class,
                 'read_only': read_only},
                 context_instance=RequestContext(request))

    else:
        return render_to_response('failure.html',
            {'message': 'The request cannot be completed as specified',
             'message-class': 'alert alert-error'},
            context_instance=RequestContext(request))

@login_required
def add_bonuses(request, qset_id):
    user = request.user.writer
    qset = QuestionSet.objects.get(id=qset_id)
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'GET':
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            form = BonusForm(qset_id=qset.id)
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
             'read_only': read_only},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        if user in qset.editor.all() or user in qset.writer.all() or user == qset.owner:
            form = BonusForm(request.POST, qset_id=qset.id)

            if form.is_valid():
                bonus = form.save(commit=False)
                bonus.author = user
                bonus.question_set = qset
                bonus.save()
                message = 'Your bonus has been successfully added to the set! Write more questions!'
                message_class = 'alert alert-success'
            else:
                print request.POST
                print form.as_p()
            read_only = False
        else:
            message = 'You are not authorized to add questions to this tournament!'
            message_class = 'alert alert-warning'
            tossup_form = []
            read_only = True

        return render_to_response('add_bonuses.html',
                 {'form': BonusForm(qset_id=qset.id),
                 'message': message,
                 'message_class': message_class,
                 'read_only': read_only},
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
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'GET':
        if user == tossup.author or user == qset.owner or user in qset.editor.all():
            form = TossupForm(instance=tossup, qset_id=qset.id)
            read_only = False

        elif user in qset.writer.all():
            read_only = True
            form = None
            message = 'You are only authorized to view, not to edit, this question!'
            message_class = 'alert alert-warning'
        else:
            tossup = None
            form = None
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert alert-danger'

        return render_to_response('edit_tossup.html',
            {'tossup': tossup,
             'form': form,
             'message': message,
             'message_class': message_class,
             'read_only': read_only},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        if user == tossup.author or user == qset.owner or user in qset.editor.all():
            form = TossupForm(request.POST, qset_id=qset.id)
            if form.is_valid():
                tossup.tossup_text = sanitize_html(form.cleaned_data['tossup_text'])
                tossup.tossup_answer = sanitize_html(form.cleaned_data['tossup_answer'])
                tossup.category = form.cleaned_data['category']
                tossup.save()
            read_only = False
        elif user in qset.writer.all():
            read_only = True
            message = 'You are only authorized to view, not to edit, this question!'
            message_class = 'alert alert-warning'
        else:
            tossup = None
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert alert-error'

        return render_to_response('edit_tossup.html',
            {'tossup': tossup,
             'form': form,
             'message': message,
             'message_class': message_class,
             'read_only': read_only},
            context_instance=RequestContext(request))

@login_required
def edit_bonus(request, bonus_id):
    user = request.user.writer
    bonus = Bonus.objects.get(id=bonus_id)
    qset = bonus.question_set
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'GET':
        if user == bonus.author or user == qset.owner or user in qset.editor.all():
            form = BonusForm(instance=bonus, qset_id=qset.id)
            read_only = False

        elif user in qset.writer.all():
            read_only = True
            message = 'You are only authorized to view, not to edit, this question!'
            message_class = 'alert alert-warning'
        else:
            bonus = None
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert alert-error'

        return render_to_response('edit_bonus.html',
            {'bonus': bonus,
             'form': form,
             'message': message,
             'message_class': message_class,
             'read_only': read_only},
            context_instance=RequestContext(request))

    elif request.method == 'POST':
        if user == bonus.author or user == qset.owner or user in qset.editor.all():
            form = BonusForm(request.POST, qset_id=qset.id)
            if form.is_valid():
                bonus.leadin = sanitize_html(form.cleaned_data['leadin'])
                bonus.part1_text = sanitize_html(form.cleaned_data['part1_text'])
                bonus.part1_answer = sanitize_html(form.cleaned_data['part1_answer'])
                bonus.part2_text = sanitize_html(form.cleaned_data['part2_text'])
                bonus.part2_answer = sanitize_html(form.cleaned_data['part2_answer'])
                bonus.part3_text = sanitize_html(form.cleaned_data['part3_text'])
                bonus.part3_answer = sanitize_html(form.cleaned_data['part3_answer'])
                bonus.category = form.cleaned_data['category']
                bonus.save()
            read_only = False
        elif user in qset.writer.all():
            read_only = True
            message = 'You are only authorized to view, not to edit, this question!'
            message_class = 'alert alert-warning'
        else:
            tossup = None
            message = 'You are not authorized to view or edit this question!'
            message_class = 'alert alert-error'

        return render_to_response('edit_tossup.html',
            {'bonus': bonus,
             'form': form,
             'message': message,
             'message_class': message_class,
             'read_only': read_only},
            context_instance=RequestContext(request))

@login_required
def delete_tossup(request, tossup_id):
    user = request.user.writer
    tossup = Tossup.objects.get(id=tossup_id)
    qset = tossup.question_set
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'GET':
        if user == tossup.author or user == qset.owner or user in qset.editor.all():
            tossup.delete()
            message = 'Tossup deleted'
            message_class = 'alert alert-success'
            read_only = False
        else:
            message = 'You are not authorized to delete questions from this set!'
            message_class = 'alert alert-warning'

    return edit_question_set(request, qset.id)

@login_required
def delete_bonus(request, bonus_id):
    user = request.user.writer
    bonus = Bonus.objects.get(id=bonus_id)
    qset = bonus.question_set
    message = ''
    message_class = ''
    read_only = True

    if request.method == 'GET':
        if user == bonus.author or user == qset.owner or user in qset.editor.all():
            bonus.delete()
            message = 'Bonus deleted'
            message_class = 'alert alert-success'
            read_only = False
        else:
            message = 'You are not authorized to delete questions from this set!'
            message_class = 'alert alert-warning'

    return edit_question_set(request, qset.id)

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
         'form': form},
        context_instance=RequestContext(request))


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

    

'''
TossupFormset = formset_factory(TossupForm)
        BonusFormset = formset_factory(BonusForm)
        player = request.user.get_profile()
        print "asdfasdfsadf"
        if request.method == 'POST':
            tu_formset = TossupFormset(request.POST, prefix='tossups')
            b_formset = BonusFormset(request.POST, prefix='bonuses')
            
            # save the tossups
            if tu_formset.is_valid():
                
                pass
            else:
                pass
            
            # save the bonuses
            if b_formset.is_valid():
                pass
            else:
                pass
            
            return render_to_response('packetedit.html',
                                          {'tu_formset': tu_formset,
                                           'b_formset': b_formset},
                                          context_instance=RequestContext(request))
        else:
             tu_formset = TossupFormset(prefix='tossups')
             b_formset = BonusFormset(prefix='bonuses')
             
        return render_to_response('packetedit.html',
                                  {'tu_formset': tu_formset,
                                   'b_formset': b_formset},
                                  context_instance=RequestContext(request))
                                  '''
@login_required
def distributions (request):
    
    data = []
    all_dists = Distribution.objects.all()
        
    return render_to_response('distributions.html',
                              {'dists': all_dists},
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
                    print dist_form.cleaned_data
                    for form in formset:
                        print form.cleaned_data
                        
                    new_dist = Distribution()
                    new_dist.name = dist_form.cleaned_data['name']
                    new_dist.save()
                    
                    for form in formset:
                        new_entry = DistributionEntry()
                        new_entry.category = form.cleaned_data['category']
                        new_entry.subcategory = form.cleaned_data['subcategory']
                        new_entry.num_bonuses = form.cleaned_data['num_bonuses']
                        new_entry.num_tossups = form.cleaned_data['num_tossups']
                        new_entry.fin_bonuses = form.cleaned_data['fin_bonuses']
                        new_entry.fin_tossups = form.cleaned_data['fin_tossups']
                        new_entry.distribution = new_dist
                        new_entry.save()
                        
            else:
                formset = DistributionEntryFormset(data=request.POST, prefix='distentry')
                dist_form = DistributionForm(data=request.POST)
                print dist_form.is_valid()
                print formset.is_valid()
                print formset.errors
                if dist_form.is_valid() and formset.is_valid():
                    
                    dist = Distribution.objects.get(id=dist_id)
                    dist.name = dist_form.cleaned_data['name']
                    for form in formset:
                        if form.cleaned_data != {}:
                            if form.cleaned_data['entry_id'] is not None:
                                entry_id = int(form.cleaned_data['entry_id'])
                                entry = DistributionEntry.objects.get(id=entry_id)
                                if form.cleaned_data['DELETE']:
                                    entry.delete()
                                else:
                                    entry.subcategory = form.cleaned_data['subcategory']
                                    entry.num_bonuses = form.cleaned_data['num_bonuses']
                                    entry.num_tossups = form.cleaned_data['num_tossups']
                                    entry.fin_bonuses = form.cleaned_data['fin_bonuses']
                                    entry.fin_tossups = form.cleaned_data['fin_tossups']
                                    entry.save()
                            else:
                                entry = form.save(commit=False)
                                entry.distribution = dist
                                entry.save()
                            
                    entries = dist.distributionentry_set.all()
                    initial_data = []
                    for entry in entries:
                        initial_data.append({'entry_id': entry.id,
                                             'category': entry.category,
                                             'subcategory': entry.subcategory,
                                             'num_tossups': entry.num_tossups,
                                             'num_bonuses': entry.num_bonuses,
                                             'fin_tossups': entry.fin_tossups,
                                             'fin_bonuses': entry.fin_bonuses})
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
                                         'num_tossups': entry.num_tossups,
                                         'num_bonuses': entry.num_bonuses,
                                         'fin_tossups': entry.fin_tossups,
                                         'fin_bonuses': entry.fin_bonuses})
                dist_form = DistributionForm(instance=dist)
                formset = DistributionEntryFormset(initial=initial_data, prefix='distentry')
            else:
                dist_form = DistributionForm()
                formset = DistributionEntryFormset(prefix='distentry')
            
            return render_to_response('edit_distribution.html',
                                      {'form': dist_form,
                                       'formset': formset},
                                       context_instance=RequestContext(request))
            
def role_assign(request, editor_id, tour_id):

    if request.method == 'POST':
        form = RoleAssignmentForm(data=request.POST)
        if form.is_valid():
            #editor_id = form.cleaned_data['editor']
            #tour_id = form.cleaned_data['tournament']
            categories = form.cleaned_data['category']
            can_edit_others = form.cleaned_data['can_edit_others']
            can_view_others = form.cleaned_data['can_view_others']
            
            categories = ';'.join(categories)
            editor = Writer.objects.get(id=editor_id)
            tournament = Tournament.objects.get(id=tour_id)
            
            role, created = Role.objects.get_or_create(player=editor,
                                                       tournament=tournament)
            role.category = categories
            role.can_edit_others = can_edit_others
            role.can_view_others = can_view_others
            role.save() 
            
            form = RoleAssignmentForm(instance=role, categories=categories.split(';'))
            
            return render_to_response('roleassign.html',
                                      {'form': form,
                                       'editor': editor,
                                       'message': 'Your changes have been successfully saved!',
                                       'message_class': 'alert-success'},
                                      context_instance=RequestContext(request))
        else:
            editor = Writer.objects.get(id=editor_id)
            
    else:
        editor = Writer.objects.get(id=editor_id)
        tour = Tournament.objects.get(id=tour_id)
        if Role.objects.filter(player=editor, tournament=tour).exists():
            role = Role.objects.get(player=editor, tournament=tour)
            categories = role.category.split(';')
            form = RoleAssignmentForm(instance=role, categories=categories)
        else:
            form = RoleAssignmentForm()
            print form.as_p()
        
    return render_to_response('roleassign.html',
                            {'form': form,
                             'editor': editor},
                              context_instance=RequestContext(request))

    
def remove_editor(request, tournament_id, editor_id):
    if request.user.is_authenticated():
        player = request.user.get_profile()
        editor = Writer.objects.get(id=editor_id)
        tournament = Tournament.objects.get(id=tournament_id)
        
        if player == tournament.owner:
            if editor in tournament.player_set.all():
                tournament.player_set.remove(editor)
                tournament.save()
                if editor.role_set.filter(tournament=tournament).exists():
                    editor_role = editor.role_set.get(tournament=tournament, player=editor)
                    editor_role.delete()
                message = 'You have removed {0!s} from your tournament.'.format(editor)
            else:
                message = '{0!s} is not an editor for this tournament.'.format(editor)
        else:
            message = 'You are not the tournament owner and are not allowed to remove editors.'
            
        form = TournamentForm(instance=tournament)
        editors = tournament.player_set.all()
        
        return HttpResponseRedirect('/touredit/{0!s}/'.format(tournament.id))
    else:
        return HttpResponseRedirect('/accounts/login/')
'''
    packet editing flow: packetedit.html renders the view that gives you the overall packet
    state of completion. that shows you what questions have been written and allows you
    to click on individual questions to edit and comment on them. there are several tabs:
    your tossups, your bonuses, others' tossups, others' bonuses, you can click on those
    to edit/comment
    '''
