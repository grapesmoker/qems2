#from __future__ import unicode_literals

from bs4 import BeautifulSoup
from models import *
from forms import *
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.contrib.contenttypes.models import ContentType
from django.contrib.comments import *

import os

def compute_packet_requirements(qset):
    '''
    :param qset: a QuestionSet model object
    :return: a collection of SetWideDistributionEntry objects
    '''

    num_packets = qset.num_packets
    packets = qset.packet_set.all()
    dist = qset.distribution
    dist_entries = dist.distributionentry_set.all()

    set_wide_entries = []

    for dist_entry in dist_entries:
        req_tus = dist_entry.min_tossups
        req_bs = dist_entry.min_bonuses

        set_wide_entry = SetWideDistributionEntry()
        set_wide_entry.category = dist_entry.category
        set_wide_entry.subcategory = dist_entry.subcategory
        set_wide_entry.num_tossups = req_tus
        set_wide_entry.num_bonuses = req_bs

        set_wide_entries.append(set_wide_entry)

    return set_wide_entries

def create_set_distro_formset(qset):

    DistributionEntryFormset = formset_factory(SetWideDistributionEntryForm, can_delete=False, extra=0)
    entries = qset.setwidedistributionentry_set.all()
    initial_data = []
    for entry in entries:
        initial_data.append({'entry_id': entry.id,
        'dist_entry': entry.dist_entry,
        'category': entry.dist_entry.category,
        'subcategory': entry.dist_entry.subcategory,
        'num_tossups': entry.num_tossups,
        'num_bonuses': entry.num_bonuses})
    return DistributionEntryFormset(initial=initial_data, prefix='distentry')

def create_tiebreak_formset(qset):

    DistributionEntryFormset = formset_factory(TieBreakDistributionEntryForm, can_delete=False, extra=0)
    entries = qset.tiebreakdistributionentry_set.all()
    initial_data = []
    for entry in entries:
        initial_data.append({'entry_id': entry.id,
        'dist_entry': entry.dist_entry,
        'category': entry.dist_entry.category,
        'subcategory': entry.dist_entry.subcategory,
        'num_tossups': entry.num_tossups,
        'num_bonuses': entry.num_bonuses})
    return DistributionEntryFormset(initial=initial_data, prefix='tiebreak')

def reset_tiebreak_distro(qset):

    dist = qset.distribution
    dist_entries = dist.distributionentry_set.all()

    old_tiebreakers = TieBreakDistributionEntry.objects.filter(question_set=qset)
    for tb in old_tiebreakers:
        tb.delete()

    for entry in dist_entries:

        tiebreak_entry = TieBreakDistributionEntry()
        tiebreak_entry.num_bonuses = 1
        tiebreak_entry.num_tossups = 1
        tiebreak_entry.question_set = qset
        tiebreak_entry.dist_entry = entry
        tiebreak_entry.save()

def get_role(user, qset):

    role = 'none'
    qset_editors = qset.editor.all()
    qset_writers = qset.writer.all()

    if user in qset_editors and user != qset.owner:
        role = 'editor'
    elif user in qset_writers:
        role = 'writer'
    elif user == qset.owner:
        role = 'owner'

    return role

def get_role_no_owner(user, qset):

    role = 'none'
    qset_editors = qset.editor.all()
    qset_writers = qset.writer.all()

    if user in qset_editors:
        role = 'editor'
    elif user in qset_writers:
        role = 'writer'

    return role    

def export_packet(packet_id):

    packet = Packet.objects.get(id=packet_id)
    qset = packet.question_set

    tex_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "tex"),)

    print tex_path

    latex_preamble = r'''
\documentclass[10pt]{article}
\usepackage[top=1in, bottom=1in, left=1in, right=1in]{geometry}
\usepackage{parskip}
\usepackage[]{graphicx}
\usepackage[normalem]{ulem}
%\usepackage{ebgaramond}
\usepackage[utf8]{inputenc}

\begin{document}

\newcommand{\ans}[1]{{\sc \uline{#1}}}

\newcommand{\tossups}{\newcounter{TossupCounter} \noindent {\sc Tossups}\\}
\newcommand{\tossup}[2]{\stepcounter{TossupCounter}
    \arabic{TossupCounter}.~#1\\ANSWER: #2\\}

\newcommand{\bonuses}{\newcounter{BonusCounter} \noindent {\sc Bonuses} \\}
% bonus part is points - text - answer
\newcommand{\bonuspart}[3]{[#1]~#2\\ANSWER: #3\\}
% bonus is leadin - parts

\newenvironment{bonus}[1]{\stepcounter{BonusCounter}
    \arabic{BonusCounter}.~#1\\}{}


%\newcommand{\bonus}[2]{\stepcounter{BonusCounter}
%  \arabic{BonusCounter}.~#1\\#2}

\begin{center}
  %\includegraphics[scale=1]{acf-logo.pdf}\\
  {\sc tournament \\ packet }
\end{center}
'''

    latex_end = r'\end{document}'

    tossups = Tossup.objects.filter(packet=packet)
    bonuses = Bonus.objects.filter(packet=packet)

    tossup_latex = r'\tossups' + '\n'
    bonus_latex = r'\bonuses' + '\n'

    output_file = os.path.join(tex_path, '{0} - {1}.tex'.format(qset, packet))

    for tossup in tossups:
        tossup_latex += tossup.to_latex()

    for bonus in bonuses:
        bonus_latex += bonus.to_latex()

    packet_latex = latex_preamble + tossup_latex + bonus_latex + latex_end

    print output_file

    print packet_latex

    f = open(output_file, 'w')
    f.write(packet_latex.encode('utf-8'))
    f.close()

def export_packet_reportlab(packet_id):

    import pdfdocument as pdf
    import io

    packet = Packet.objects.get(id=packet_id)
    qset = packet.question_set

    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "pdf"),)
    
# Edits all of these questions
def bulk_edit_questions(is_edited, tossups, bonuses, qset, user):
    for tossup in tossups:
        tossup.edited = is_edited
        tossup.save_question(QUESTION_EDIT, user)
        
    for bonus in bonuses:
        bonus.edited = is_edited
        bonus.save_question(QUESTION_EDIT, user)
        
def bulk_lock_questions(is_locked, tossups, bonuses, qset, user):
    for tossup in tossups:
        tossup.locked = is_locked
        tossup.save_question(QUESTION_EDIT, user)
        
    for bonus in bonuses:
        bonus.locked = is_locked
        bonus.save_question(QUESTION_EDIT, user)    

def bulk_delete_questions(tossups, bonuses, qset, user):
    for tossup in tossups:
        tossup.delete()
        
    for bonus in bonuses:
        bonus.delete()

def bulk_convert_to_acf_style_tossup(tossups, bonuses, qset, user):
    for tossup in tossups:
        tossup_to_tossup(tossup, ACF_STYLE_TOSSUP)
    
    for bonus in bonuses:
        bonus_to_tossup(bonus, ACF_STYLE_TOSSUP)

def bulk_convert_to_acf_style_bonus(tossups, bonuses, qset, user):
    for tossup in tossups:
        tossup_to_bonus(tossup, ACF_STYLE_BONUS)
    
    for bonus in bonuses:
        bonus_to_bonus(bonus, ACF_STYLE_BONUS)

def bulk_convert_to_vhsl_bonus(tossups, bonuses, qset, user):
    for tossup in tossups:
        tossup_to_bonus(tossup, VHSL_BONUS)
    
    for bonus in bonuses:
        bonus_to_bonus(bonus, VHSL_BONUS)

def tossup_to_bonus(tossup, output_question_type):
    if (output_question_type == ACF_STYLE_BONUS):
        if (tossup.get_tossup_type() == ACF_STYLE_TOSSUP):
            bonus = copy_to_bonus(tossup)
            bonus.question_type = QuestionType.objects.get(question_type=ACF_STYLE_BONUS)
            bonus.leadin = tossup.tossup_text
            bonus.part1_answer = tossup.tossup_answer
            bonus.part1_text = ""
            bonus.part2_text = ""
            bonus.part2_answer = ""
            bonus.part3_text = ""
            bonus.part3_answer = ""
            bonus.save()
            move_comments_to_bonus(tossup, bonus)                        
            tossup.delete()
    elif (output_question_type == VHSL_BONUS):
        if (tossup.get_tossup_type() == ACF_STYLE_TOSSUP):
            bonus = copy_to_bonus(tossup)
            bonus.part1_text = tossup.tossup_text
            bonus.part1_answer = tossup.tossup_answer
            bonus.question_type = QuestionType.objects.get(question_type=VHSL_STYLE_BONUS)            
            bonus.leadin = ""
            bonus.part2_text = ""
            bonus.part2_answer = ""
            bonus.part3_text = ""
            bonus.part3_answer = ""
            bonus.save()
            move_comments_to_bonus(tossup, bonus)            
            tossup.delete()                  
        
def tossup_to_tossup(tossup, output_question_type):
    pass # No-op for now since there's just one type of tossup

def bonus_to_bonus(bonus, output_question_type):
    print "bonus to bonus"
    if (output_question_type == ACF_STYLE_BONUS):
        if (bonus.get_bonus_type() == VHSL_BONUS):
            print "Convert to ACF"
            bonus.question_type = QuestionType.objects.get(question_type=ACF_STYLE_BONUS)
            bonus.leadin = ""
            bonus.part2_text = ""
            bonus.part2_answer = ""
            bonus.part3_text = ""
            bonus.part3_answer = ""
            bonus.save()
    elif (output_question_type == VHSL_BONUS):
        if (bonus.get_bonus_type() == ACF_STYLE_BONUS):
            print "Convert to VHSL"
            bonus.question_type = QuestionType.objects.get(question_type=VHSL_BONUS)
            bonus.part1_text = bonus.leadin + " " + bonus.part1_text + " " + bonus.part1_answer + " " + bonus.part2_text + " " + bonus.part2_answer + " " + bonus.part3_text + " " + bonus.part3_answer
            bonus.leadin = ""
            bonus.part2_text = ""
            bonus.part2_answer = ""
            bonus.part3_text = ""
            bonus.part3_answer = ""            
            bonus.save()            
        
def bonus_to_tossup(bonus, output_question_type):
    if (output_question_type == ACF_STYLE_TOSSUP):
        if (bonus.get_bonus_type() == VHSL_BONUS):
            tossup = copy_to_tossup(bonus)
            tossup.question_type = QuestionType.objects.get(question_type=ACF_STYLE_TOSSUP)
            tossup.tossup_text = bonus.part1_text
            tossup.tossup_answer = bonus.part1_answer
            tossup.save()
            move_comments_to_tossup(bonus, tossup)
            bonus.delete()            
        elif (bonus.get_bonus_type() == ACF_STYLE_BONUS):
            tossup = copy_to_tossup(bonus)
            tossup.question_type = QuestionType.objects.get(question_type=ACF_STYLE_TOSSUP)
            tossup.tossup_text = bonus.leadin + " " + bonus.part1_text + " " + bonus.part1_answer + " " + bonus.part2_text + " " + bonus.part2_answer + " " + bonus.part3_text + " " + bonus.part3_answer
            tossup.tossup_answer = bonus.part1_answer
            tossup.save()
            move_comments_to_tossup(bonus, tossup)            
            bonus.delete()                        
        
def copy_to_tossup(bonus):
    tossup = Tossup()
    tossup.packet = bonus.packet
    tossup.question_set = bonus.question_set
    tossup.category = bonus.category
    tossup.subtype = bonus.subtype
    tossup.time_period = bonus.time_period
    tossup.location = bonus.location
    tossup.author = bonus.author
    tossup.question_history = bonus.question_history
    tossup.created_date = bonus.created_date
    tossup.last_changed_date = bonus.last_changed_date
    return tossup

def move_comments_to_tossup(bonus, tossup):
    # Change all of the comments to be associated with this new object
    tossup_content_type_id = ContentType.objects.get(name="tossup")
    bonus_content_type_id = ContentType.objects.get(name="bonus")
    for comment in Comment.objects.filter(object_pk=bonus.id).filter(content_type_id=bonus_content_type_id):
        comment.object_pk = tossup.id
        comment.content_type_id = tossup_content_type_id
        comment.save()

def copy_to_bonus(tossup):
    bonus = Bonus()
    bonus.packet = tossup.packet
    bonus.question_set = tossup.question_set
    bonus.category = tossup.category
    bonus.subtype = tossup.subtype
    bonus.time_period = tossup.time_period
    bonus.location = tossup.location
    bonus.author = tossup.author
    bonus.question_history = tossup.question_history
    bonus.created_date = tossup.created_date
    bonus.last_changed_date = tossup.last_changed_date
    return bonus

def move_comments_to_bonus(tossup, bonus):
    # Change all of the comments to be associated with this new object
    tossup_content_type_id = ContentType.objects.get(name="tossup")
    bonus_content_type_id = ContentType.objects.get(name="bonus")
    for comment in Comment.objects.filter(object_pk=tossup.id).filter(content_type_id=tossup_content_type_id):
        comment.object_pk = bonus.id
        comment.content_type_id = bonus_content_type_id
        comment.save()

def get_question_type_from_string(question_type):
    return QuestionType.objects.get(question_type=question_type)

def get_tossup_and_bonuses_in_set(qset, question_limit=30, preview_only=False):
    tossup_dict = {}
    tossups = []
    tossup_count = 0
    for tossup in Tossup.objects.filter(question_set=qset).order_by('-id'):
        if (tossup_count < question_limit):
            if (preview_only):
                tossup.tossup_text = preview(tossup.tossup_text)
                tossup.tossup_answer = preview(get_primary_answer(tossup.tossup_answer))
            
            tossups.append(tossup)            
            tossup_count += 1
        tossup_dict[tossup.id] = tossup

    bonus_dict = {}
    bonuses = []
    short_bonuses = []
    bonus_count = 0
    for bonus in Bonus.objects.filter(question_set=qset).order_by('-id'):
        if (bonus_count < question_limit):
            if (preview_only):
                bonus.leadin = preview(bonus.leadin)
                bonus.part1_text = preview(bonus.part1_text)
                bonus.part1_answer = preview(get_primary_answer(bonus.part1_answer))
                bonus.part2_text = preview(bonus.part2_text)
                bonus.part2_answer = preview(get_primary_answer(bonus.part2_answer))
                bonus.part3_text = preview(bonus.part3_text)
                bonus.part3_answer = preview(get_primary_answer(bonus.part3_answer))
            
            bonuses.append(bonus)
            bonus_count += 1
        bonus_dict[bonus.id] = bonus
        
    return tossups, tossup_dict, bonuses, bonus_dict

def get_comment_tab_list(tossup_dict, bonus_dict):
    comment_tab_list = []
    
    tossup_content_type_id = ContentType.objects.get(name="tossup")
    bonus_content_type_id = ContentType.objects.get(name="bonus")
    
    comment_count = 0
    for comment in Comment.objects.filter(content_type_id=tossup_content_type_id).order_by('-submit_date'):
        if (long(comment.object_pk) in tossup_dict):
            tossup = tossup_dict[long(comment.object_pk)]            
            new_comment = { 'comment': comment,
                                'question_text': get_formatted_question_html(tossup.tossup_answer[0:80], True, True, False),
                                'question_id': tossup.id,
                                'question_type': 'tossup'}
            comment_tab_list.append(new_comment)
            comment_count += 1
            if (comment_count >= 30):
                break

    comment_count = 0
    for comment in Comment.objects.filter(content_type_id=bonus_content_type_id).order_by('-submit_date'):
        if (long(comment.object_pk) in bonus_dict):
            bonus = bonus_dict[long(comment.object_pk)]            
            new_comment = { 'comment': comment,
                                'question_text': get_formatted_question_html_for_bonus_answers(bonus),
                                'question_id': bonus.id,
                                'question_type': 'bonus'}
            comment_tab_list.append(new_comment)
            comment_count += 1
            if (comment_count >= 30):
                break
    
    return comment_tab_list

