from django.template.loader import get_template
from django.template import Context, RequestContext
from django.shortcuts import render_to_response
from django import forms
from django.forms.formsets import formset_factory
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import ListView
from django.utils import simplejson
from django.contrib.auth.models import User

from models import *
from forms import *

from collections import OrderedDict
from itertools import chain


def register (request):
    if request.method == 'POST':
        form = PlayerCreationForm(request.POST)
        
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect("/main/")
    else:
        form = PlayerCreationForm()
    return render_to_response('registration/register.html',
                              {'form': form,},
                              context_instance=RequestContext(request))

def main (request):
    if request.user.is_authenticated():
        return render_to_response('main.html', {'user': request.user},
                                  context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect("/accounts/login/")
        #return HttpResponse('<font color="red">bad shit happened</font>')
    
def tourview(request):
    
    if request.user.is_authenticated():
        return render_to_response('tourview.html', {}, context_instance=RequestContext(request))
    else:
        return HttpResponse('<font color="red">You are not authorized to view this page</font>')
    
def tour(request):
    if request.user.is_authenticated():
        player = request.user.get_profile()
        # collect all tournaments owned by player
        owned_tournaments = Tournament.objects.filter(owner=player)
        # now get all the tournaments this player is an editor on
        editor_tournaments = player.tournament.all()
        # now get all the tournaments this player is not part of but which are also not public
        available_tournaments = Tournament.objects.exclude(owner=player).exclude(public=True)
        joinable_tournaments = [tour for tour in available_tournaments if tour not in editor_tournaments]
        # now finally all public tournaments (can overlap with above?)
        public_tournaments = Tournament.objects.filter(public=True)
        
        all_tournaments = [{'header': 'Tournaments you own', 'tours': owned_tournaments, 'id': 'tour-owned'},
                           {'header': 'Tournaments you are editing', 'tours': editor_tournaments, 'id': 'tour-edit'},
                           {'header': 'Tournaments you can ask to join', 'tours': joinable_tournaments, 'id': 'tour-avail'},
                           {'header': 'Public tournaments', 'tours': public_tournaments, 'id': 'tour-public'}]
        
        return render_to_response('tourview.html', 
                                  {'tournament_list': all_tournaments},
                                  context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect("/accounts/login/")
    
def school(request):
    if request.user.is_authenticated():
        player = request.user.get_profile()
        all_schools = School.objects.all()
        
        return render_to_response('schoolview.html',
                                  {'school_list': all_schools},
                                  context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/accounts/login/')
    
def school_info(request, school_id):
    if request.user.is_authenticated():
        
        if request.method == 'POST':
            form = SchoolForm(data=request.POST, read_only=False)
            if form.is_valid():
                school = School.objects.get(id=school_id)
                school.name = form.cleaned_data['name']
                school.address = form.cleaned_data['address']
                school.contact = form.cleaned_data['contact']
                school.contact_email = form.cleaned_data['contact_email']
                school.contact_phone = form.cleaned_data['contact_phone']
                school.save()
                
                return render_to_response('schoolinfo.html',
                                          {'form': form,
                                           'school_id': school_id,
                                           'read_only': False,
                                           'message': 'Your changes have been successfully saved',
                                           'message_class': 'alert-success'},
                                          context_instance=RequestContext(request))
                
            else:
                return render_to_response('schoolinfo.html',
                                  {'form': form,
                                   'school_id': school_id,
                                   'read_only': False,
                                   'message': 'There were errors saving the changes.',
                                   'message_class': 'alert-error'},
                                  context_instance=RequestContext(request))
        
        else:
            player = request.user.get_profile()
            school = School.objects.get(id=school_id)
            read_only = True
            if school.created_by == player:
                read_only = False
            form = SchoolForm(instance=school, read_only=read_only)
        
        return render_to_response('schoolinfo.html',
                                  {'form': form,
                                   'school_id': school_id,
                                   'read_only': read_only},
                                  context_instance=RequestContext(request))
        
    else:
        return HttpResponseRedirect('/accounts/login/')

def create_school(request):
    if request.user.is_authenticated():
        if request.method == 'POST':
            print 'post'
            print request.POST
            form = SchoolForm(data=request.POST, read_only=False)
            if form.is_valid():
                print 'valid'
                player = request.user.get_profile()
                school = form.save(commit=False)
                school.created_by = player
                school.save()
                
                return render_to_response('success.html',
                                          {'message': 'Your school has been added to the database.'},
                                          context_instance=RequestContext(request))
            else:
                print 'not valid'
                print form.errors
                pass
        else:
            print 'not post'
            form = SchoolForm()
        
        print 'return'
        print form
        print form.non_field_errors()
        return render_to_response('schoolcreate.html',
                                  {'form': form},
                                  context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect('/accounts/login/')
        
def school_edit(request):
    pass

    
def team(request):
    if request.user.is_authenticated():
        player = request.user.get_profile()
        owned_teams = Team.objects.filter(team_owner=player)
        member_teams = player.team.all()
        joinable_teams = [team for team in Team.objects.all() if team not in owned_teams and team not in member_teams]
        
        all_teams = [{'header': 'Teams you created', 'teams': owned_teams, 'id': 'teams-owned'},
                     {'header': 'Teams you are a member of', 'teams': member_teams, 'id': 'teams-member'},
                     {'header': 'Teams you can request to join', 'teams': joinable_teams, 'id': 'teams-avail'}]
        
        return render_to_response('teamview.html',
                                  {'team_list': all_teams},
                                  context_instance=RequestContext(request)) 
    else:
        return HttpResponseRedirect('/accounts/login/')

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
        

def create_tournament(request):
    if request.method == 'POST':
        form = TournamentForm(data=request.POST)
        print form
        if form.is_valid():
            player = request.user.get_profile()
            tournament = form.save(commit=False)
            tournament.owner = player
            tournament.save()
            tournament.player_set.add(player)
            tournament.save()
            #tournament.save_m2m()
            
            return render_to_response('success.html',
                                      {'message': 'Your tournament has been successfully created!'},
                                      context_instance=RequestContext(request))
        else:
            print form.errors
            return render_to_response('failure.html',
                                      {'message': 'There was an error in creating your tournament!'},
                                      context_instance=RequestContext(request))
    else:
        form = TournamentForm()
        
    return render_to_response('tourcreate.html',
                              {'form': form},
                              context_instance=RequestContext(request))
    
def editor_create_packet(request, tour_id):
    if request.user.is_authenticated():
        player = request.user.get_profile()
        tour = Tournament.objects.get(id=tour_id)
        
        if player != tour.owner:
            return render_to_response('failure.html',
                                      {'message': 'You cannot create a packet unless you are the tournament owner!'},
                                      context_instance=RequestContext(request))
        
        packet = Packet()
        packet.tournament = tour
        packet.created_by = player
        

def create_packet(request, team_id):
    if request.user.is_authenticated():
        if team_id is None:
            return render_to_response('failure.html',
                                      {'message': 'Team ID required to create packet!'},
                                      context_instance=RequestContext(request))
            
        player = request.user.get_profile()
        print player, player.id, team_id
        team = Team.objects.get(id=team_id)
        
        # check to make sure this player belongs to this team
        if player != team.team_owner:
            return render_to_response('failure.html',
                                      {'message': 'You cannot create a packet unless you are the team manager!'},
                                      context_instance=RequestContext(request))
        # don't create multiple packets; editor packet creation handled separately
        if len(team.packet_set.all()) != 0:
            return render_to_response('failure.html',
                                      {'message': 'A packet already exists for this team and tournament!'},
                                      context_instance=RequestContext(request))
            
        packet = Packet()
        packet.tournament = team.tournament
        packet.team = team
        packet.created_by = player
        packet.save()
        packet.authors = team.player_set.all()
        packet.authors.add(player)
        packet.save()
        form = TeamForm(instance=team)
        
        return render_to_response('teamedit.html',
                                  {'form': form,
                                   'teammates': team.player_set.all(),
                                   'packets': team.packet_set.all(),
                                   'team': team,
                                   'message': 'Your packet has been created!',
                                   'message_type': 'success',
                                   'player': player},
                                  context_instance=RequestContext(request))
        
    else:
        return HttpResponseRedirect('/accounts/login/')

def create_team(request):
    if request.method == 'POST':
        print request.POST
        form = TeamForm(data=request.POST)
        if form.is_valid():
            player = request.user.get_profile()
            school = form.cleaned_data['school']
            tournament = form.cleaned_data['tournament']
            
            team = form.save(commit=False)
            team.team_owner = player
            existing_team = Team.objects.filter(school=school, tournament=tournament)
            
            if existing_team is not None:
                return render_to_response('failure.html',
                                          {'message': 'A team with that name already exists for this tournament!'},
                                          context_instance=RequestContext(request))
            
            team.save()
            
            return render_to_response('success.html',
                                      {'message': 'Your team has been successfully created!'},
                                      context_instance=RequestContext(request))
    else:
        form = TeamForm()
        
    return render_to_response('teamcreate.html',
                              {'form': form},
                              context_instance=RequestContext(request))

def edit_team(request, team_id):
    
    read_only = False
    message = ''
    player = request.user.get_profile()
    
    if request.method == 'POST':
        form = TeamForm(data=request.POST)
        if form.is_valid():
            team = Team.objects.get(id=team_id)
            try:
                teammate_to_add_id = request.POST.get('hd_teammate_to_add')
                teammate = Player.objects.get(id=teammate_to_add_id)
                team.player_set.add(teammate)
                if team.packet_set.all().exists():
                    packet = team.packet_set.all()[0]
                    packet.authors.add(teammate)
            except Exception as ex:
                print ex
            team.team_name = form.cleaned_data['team_name']
            team.tournament = form.cleaned_data['tournament']
            team.school = form.cleaned_data['school']
            
            team.save()
            
            packets = team.packet_set.all()
            
            return render_to_response('teamedit.html',
                                      {'form': form,
                                       'teammates': team.player_set.all(),
                                       'team': team,
                                       'packets': packets,
                                       'message': 'Your changes have been successfully saved!',
                                       'message_type': 'success',
                                       'player': player},
                                      context_instance=RequestContext(request))
        else:
            teammates = []
    else:
        team = Team.objects.get(id=team_id)
        teammates = team.player_set.all()
        packets = team.packet_set.all()
        
        if request.user.get_profile() != team.team_owner:
            form = TeamForm(instance=team, read_only=True)
            read_only = True
            message = 'You are not authorized to edit this team information.'
        else:
            form = TeamForm(instance=team)
            
    return render_to_response('teamedit.html',
                              {'form': form,
                               'teammates': teammates,
                               'team': team,
                               'packets': packets,
                               'read_only': read_only,
                               'message': message,
                               'player': player},
                              context_instance=RequestContext(request))

def edit_tournament(request, tour_id):
    print tour_id
    read_only = False
    message = ''
    
    if request.method == 'POST':
        print request.POST
        form = TournamentForm(data=request.POST)
        if form.is_valid():
            tournament = Tournament.objects.get(id=tour_id)
            try:
                editor_to_add_id = request.POST.get('hd_player_to_add')
                print request.POST
                print editor_to_add_id
                player = Player.objects.get(id=editor_to_add_id)
                tournament.player_set.add(player)
            except Exception as ex:
                print ex
            tournament.name = form.cleaned_data['name']
            tournament.date = form.cleaned_data['date']
            tournament.host = form.cleaned_data['host']
            tournament.address = form.cleaned_data['address']
            
            tournament.save()
            
            return render_to_response('touredit.html',
                                      {'form': form,
                                       'tour': tournament,
                                       'editors': tournament.player_set.all(),
                                       'packets': tournament.packet_set.all(), 
                                       'message': 'Your changes have been successfully saved.',
                                       'message_class': 'alert-success'},
                                      context_instance=RequestContext(request))
        else:
            tournament_editors = []
    else:
        tournament = Tournament.objects.get(id=tour_id)
        tournament_editors = tournament.player_set.all()
        if request.user.get_profile() not in tournament_editors and request.user.get_profile() != tournament.owner:
            form = TournamentForm(instance=tournament, read_only=True)
            read_only = True
            message = 'You are not authorized to edit this tournament.'
        else:
            form = TournamentForm(instance=tournament)
        
        
    return render_to_response('touredit.html',
                              {'form': form,
                               'editors': tournament_editors,
                               'packets': tournament.packet_set.all(),
                               'tour': tournament,
                               'tour_id': tour_id,
                               'read_only': read_only,
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

def question_view(request, type, packet_id):
    
    if type != 'tossup' and type != 'bonus':
        return render_to_response('failure.html',
                                  {'message': 'Invalid question type!',
                                   'message_type': 'error'})
    
    if request.user.is_authenticated():
        player = request.user.get_profile()
        packet = Packet.objects.get(id=packet_id)
        team = packet.team
        
        if type == 'tossup':
            question_set = packet.tossup_set.all()
        elif type == 'bonus':
            question_set = packet.bonus_set.all()
            
        questions_authored = []
        questions_to_edit = []
        questions_to_view = []
        
        # is the player allowed to view/edit?
        # if he has any kind of role, show him that
        
        if TeamRole.objects.filter(team=team, player=player).exists():
            player_role = TeamRole.objects.get(team=team, player=player)
            for question in question_set:
                if question.author == player:
                    questions_authored.append(question)
                elif question.author != player and player_role.can_edit_others:
                    questions_to_edit.append(question)
                elif question.author != player and player_role.can_view_others:
                    questions_to_view.append(question)
        # otherwise just show the stuff he wrote
        else:
            player_role = None
            for question in question_set:
                if question.author == player:
                    questions_authored.append(question)
                    
        return render_to_response('questionview.html',
                                  {'questions_authored': questions_authored,
                                   'questions_to_edit': questions_to_edit,
                                   'questions_to_view': questions_to_view,
                                   'role': player_role,
                                   'player': player,
                                   'packet': packet,
                                   'team': team,
                                   'type': type},
                                  context_instance=RequestContext(request))
                    
            
    else:
        return HttpResponseRedirect('/accounts/login/')
    pass


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

def players_in_tournament(tournament):
    
    teams = tournament.team_set.all()
    players = []
    for team in teams:
        for player in team.player_set.all():
            players.append(player)
            
    return players

def find_player(request):
    data = []
    if request.user.is_authenticated():
        if request.is_ajax() and request.method == 'GET':
            player = request.user.get_profile()
            term = request.GET.get('term', '')
            tour_id = request.GET.get('tour_id', '')
            tournament = Tournament.objects.get(id=tour_id)
            players_playing = players_in_tournament(tournament)
            available_editors = Player.objects.exclude(id=player.id).exclude(tournament=tournament).filter(user__username__startswith=term)
            for editor in available_editors:
                if editor not in players_playing:
                    data.append({'label': editor.user.username, 'value': editor.id})
    else:
        print 'User not authenticated'
    return HttpResponse(simplejson.dumps(data), 'application/json')

def find_teammate(request):
    data = []
    print 'finding teammate'
    if request.user.is_authenticated():
        if request.is_ajax() and request.method == 'GET':
            player = request.user.get_profile()
            term = request.GET.get('term', '')
            team_id = request.GET.get('team_id', '')
            team = Team.objects.get(id=team_id)
            
            players_on_team = team.player_set.all()
            print 'butts'
            players_playing = players_in_tournament(team.tournament) 
            
            available_teammates = Player.objects.exclude(id=player.id).filter(user__username__startswith=term)
            for teammate in available_teammates:
                if teammate not in players_playing:
                    data.append({'label': teammate.user.username, 'value': teammate.id})
    else:
        print 'User not authenticated'
    return HttpResponse(simplejson.dumps(data), 'application/json')


def get_tournament_players(request):
    data = []
    
    if request.user.is_authenticated():
        if request.is_ajax() and request.method == 'POST':
            tour_id = request.POST.get('tour_id', '')
            tour = Tournament.objects.get(id=tour_id)
            players = tour.player_set.all()
            for player in players:
                data.append({'label': player.user.username, 'value': editor.id})
    return HttpResponse(simplejson.dumps(data), 'application/json')
            
def distributions(request):
    
    data = []
    if request.user.is_authenticated():
        all_dists = Distribution.objects.all()
        
        return render_to_response('distributions.html',
                                  {'dists': all_dists},
                                  context_instance=RequestContext(request))
        
    else:
        return HttpResponseRedirect('/accounts/login/')
            
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
                    
            return render_to_response('editdistribution.html',
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
            
            return render_to_response('editdistribution.html',
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
            editor = Player.objects.get(id=editor_id)
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
            editor = Player.objects.get(id=editor_id)
            
    else:
        editor = Player.objects.get(id=editor_id)
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
    
def team_role_assign(request, writer_id, team_id):
    
    if request.method == 'POST':
        form = TeamRoleAssignmentForm(data=request.POST)
        if form.is_valid():
            categories = form.cleaned_data['category']
            can_edit_others = form.cleaned_data['can_edit_others']
            can_view_others = form.cleaned_data['can_view_others']
            
            categories = ';'.join(categories)
            writer = Player.objects.get(id=writer_id)
            team = Team.objects.get(id=team_id)
            
            team_role, created = TeamRole.objects.get_or_create(player=writer,
                                                       team=team)
            team_role.category = categories
            team_role.can_edit_others = can_edit_others
            team_role.can_view_others = can_view_others
            team_role.save() 
            
            form = TeamRoleAssignmentForm(instance=team_role, categories=categories.split(';'))
            
            return render_to_response('teamroleassign.html',
                                      {'form': form,
                                       'writer': writer},
                                      context_instance=RequestContext(request))
        else:
            writer = Player.objects.get(id=writer_id)
            
    else:
        writer = Player.objects.get(id=writer_id)
        team = Team.objects.get(id=team_id)
        if TeamRole.objects.filter(player=writer, team=team).exists():
            team_role = TeamRole.objects.get(player=writer, team=team)
            categories = team_role.category.split(';')
            form = TeamRoleAssignmentForm(instance=team_role, categories=categories)
        else:
            form = TeamRoleAssignmentForm()
        
    return render_to_response('teamroleassign.html',
                            {'form': form,
                             'writer': writer},
                              context_instance=RequestContext(request))
    
def remove_teammate(request, team_id, teammate_id):
    if request.user.is_authenticated():
        print teammate_id
        player = request.user.get_profile()
        teammate = Player.objects.get(id=teammate_id)
        team = Team.objects.get(id=team_id)
        
        if player == team.team_owner:
            if teammate in team.player_set.all():
                team.player_set.remove(teammate)
                team.save()
                if teammate.teamrole_set.filter(team_id=team.id).exists():
                    teammate_role = teammate.teamrole_set.get(team_id=team.id, player_id=teammate.id)
                    teammate_role.delete()
                message = 'You have removed {0!s} from your team.'.format(teammate)
            else:
                message = '{0!s} is not on your team.'.format(teammate)
        else:
            message = 'You are not the team manager and are not allowed to remove players.'
            
        form = TeamForm(instance=team)
        teammates = team.player_set.all()
        
        return HttpResponseRedirect('/teamedit/{0!s}/'.format(team.id))
    else:
        return HttpResponseRedirect('/accounts/login/')
    
def remove_editor(request, tournament_id, editor_id):
    if request.user.is_authenticated():
        player = request.user.get_profile()
        editor = Player.objects.get(id=editor_id)
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
