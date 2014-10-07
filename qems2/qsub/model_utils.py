#from __future__ import unicode_literals

from bs4 import BeautifulSoup
from models import *
from forms import *
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory

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

def get_role(user, qset):

    role = 'viewer'
    qset_editors = qset.editor.all()
    qset_writers = qset.writer.all()

    if user in qset_editors and user != qset.owner:
        role = 'editor'
    elif user in qset_writers:
        role = 'writer'
    elif user == qset.owner:
        role = 'owner'

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


