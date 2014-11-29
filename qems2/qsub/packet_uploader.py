# This file contains a bunch of upload packet parsing methods that
# I (Bentley) haven't fixed yet to work with the refactoring

__author__ = 'jerry'

import re
import json
import string

from qems2.qsub.utils import are_special_characters_balanced, does_answerline_have_underlines
from qems2.qsub.model_utils import sanitize_html
from django.utils.html import escape

ansregex = '(?i)a..?wers?:\s*'
bpart_regex = '^\[\d+\]'
vhsl_bpart_regex = '^\[V\d+\]'
category_regex = '\{(.+)}'
bonus_value_regex = '\[|\]|\(|\)'

def parse_uploaded_packet(uploaded_file):

    print uploaded_file.name
    file_data = uploaded_file.read().split('\n')

    tossups, bonuses, tossup_errors, bonus_errors = parse_packet_data(file_data)

    return tossups, bonuses


def handle_uploaded_packet(uploaded_file):

    print uploaded_file.name

    file_data = uploaded_file.read().split('\n')

    first_tossup = find_first_tossup(file_data)
    first_bonus = find_first_bonus(file_data)

    try:
        last_tossup = find_last_tossup(file_data, first_bonus)
    except:
        last_tossup = None
        first_tossup = None

    try:
        last_bonus = find_last_bonus(file_data)
    except:
        last_bonus = None
        first_bonus = None

    print first_tossup, last_tossup

    if first_tossup is not None and last_tossup is not None:
        tossups = file_data[first_tossup:last_tossup]
    else:
        tossups = []

    if first_bonus is not None and last_bonus is not None:
        bonuses = file_data[first_bonus:last_bonus]
    else:
        bonuses = []

    #print last_bonus

    cleaned_tossups = [line for line in tossups if len(line) > 7]
    cleaned_bonuses = [line for line in bonuses if len(line) > 7]

    #print cleaned_tossups

    final_tossups, tu_errors = tossups_structured(cleaned_tossups)
    final_bonuses, bs_errors = bonuses_structured(cleaned_bonuses)

    #print final_tossups

    return final_tossups, final_bonuses


def find_first_tossup (text):

    first_index = next((i for i in range(len(text)) if re.search(ansregex, text[i], re.I)), None)
    return first_index - 1


def find_first_bonus (text):
    first_index = next((i for i in range(len(text)) if re.search(bpart_regex, text[i], re.I)), None)
    #this actually finds the first bonus part
    #so return that index - 1 to get the first bonus leadin
    return first_index - 1


def find_last_tossup (text, first_bonus_index):
    reversed = text[0:first_bonus_index][::-1]
    last_index = len(reversed) - find_first_tossup(reversed)
    return last_index - 1


def find_last_bonus (text):
    reversed = text[::-1]
    last_index = len(reversed) - find_first_bonus(reversed)
    return last_index


def tossup_filter(tossups):

    tossups = map(lambda text: string.strip(re.sub('^\d*\.', '', text)), tossups)
    #tossups = map(lambda text: re.sub('\'', '\\\'', text), tossups)
    questions = [tossups[i] for i in range(len(tossups)) if i % 2 == 0]
    questions = map(lambda text: string.strip(re.sub('^\d*\.', '', text)), questions)
    answers = [tossups[i] for i in range(len(tossups)) if i % 2 == 1]
    answers = [tossups[i] for i in range(len(tossups)) if i % 2 == 1]
    answers = map(lambda text: re.sub(ansregex, '', text, re.I), answers)
    answers = map(lambda text: string.strip(text), answers)
    answers = map(lambda text: sanitize_html(text, ['u', 'b', 'i']), answers)
    #answers = map(lambda text: re.sub('(?i)<b><u>|<u><b>', '<req>', text), answers)
    #answers = map(lambda text: re.sub('(?i)</b></u>|</u></b>', '</req>', text), answers)

    return tossups, questions, answers

def tossups_structured(tossups, mode='json'):

    errors = 0

    tossups, questions, answers = tossup_filter(tossups)

    tossups_text = ''

    tossup_objects = []

    for i, (question, answer) in enumerate(zip(questions, answers)):
        tossup = Tossup(question, answer, i + 1)
        if mode == 'json':
            tossups_text += tossup.to_json() + ','
        elif mode == 'latex':
            tossups_text += tossup.to_latex() + '\n'
        try:
            tossup.is_valid()
            tossup_objects.append(tossup)
        except InvalidTossup as ex:
            print ex
            print tossup
            errors += 1

    if mode == 'json':
        tossups_text = '"tossups": [' + tossups_text[:-1] + ']' + '\n'
    elif mode == 'latex':
        tossups_text = r'\tossups' + '\n' + tossups_text[:-1] + '\n'

    return tossup_objects, errors

def bonuses_structured(bonuses, mode='json'):

    errors = 0

    bonuses_text = ''
    bonuses = map(lambda text: string.strip(re.sub('^\d*\.', '', text)), bonuses)
    bonus_objects = []
    #bonuses = map(lambda text: re.sub('\'', '\\\'', text), bonuses)
    leadin_markers = [i for i in range(len(bonuses)) if not re.search('^\[\w*\]|^\(\w*\)|(?i)^(answer|asnwer|answers|anwer):', bonuses[i])]
    print leadin_markers
    for i in range(len(leadin_markers)):
        leadin = bonuses[leadin_markers[i]]
        parts = []
        values = []
        answers = []

        if leadin_markers[i] < leadin_markers[-1]:
            b_index = i + 1
            current_bonus = bonuses[leadin_markers[i] + 1:leadin_markers[b_index]]
        else:
            b_index = i
            current_bonus = bonuses[leadin_markers[b_index] + 1:]


        #print current_bonus
        for element in current_bonus:
            element = string.strip(element)
            if re.search(ansregex, element):
                answer = string.strip(re.sub(ansregex, '', element))
                answer = sanitize_html(answer, ['u', 'b', 'i'])
                answer = re.sub('(?i)<b><u>|<u><b>', '<req>', answer)
                answer = re.sub('(?i)</b></u>|</u></b>', '</req>', answer)
                answers.append(answer)
            else:
                match = re.search('^(\[\w*\]|\(\w*\))', element)
                val = re.sub('\[|\]|\(|\)', '', match.group(0))
                question = string.strip(re.sub('^(\[\w*\]|\(\w*\))', '', element))
                question = sanitize_html(question, ['i'])
                parts.append(question)
                values.append(val)

        bonus = Bonus(leadin, parts, answers, values, i + 1)
        if mode == 'json':
            bonuses_text += bonus.to_json() + ','
        elif mode == 'latex':
            bonuses_text += bonus.to_latex() + '\n'
        try:
            bonus.is_valid()
            bonus_objects.append(bonus)
        except InvalidBonus as ex:
            print ex
            print bonus
            errors += 1

    if mode == 'json':
        bonuses_text = '"bonuses": [' + bonuses_text[:-1] + ']' + '\n'
    elif mode == 'latex':
        bonuses_text = r'\bonuses ' + '\n' + bonuses_text

    return bonus_objects, errors
