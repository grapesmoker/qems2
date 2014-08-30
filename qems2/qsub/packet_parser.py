__author__ = 'jerry'

import re
import json
import string

from qems2.qsub.utils import sanitize_html

ansregex = '(?i)a..?wers?:'


def handle_uploaded_packet(uploaded_file):

    print uploaded_file.name

    file_data = uploaded_file.read().split('\n')

    first_tossup = find_first_tossup(file_data)
    first_bonus = find_first_bonus(file_data)

    last_tossup = find_last_tossup(file_data, first_bonus)
    last_bonus = find_last_bonus(file_data)

    tossups = file_data[first_tossup:last_tossup]
    bonuses = file_data[first_bonus:last_bonus]

    #print last_bonus

    cleaned_tossups = [line for line in tossups if len(line) > 7]
    cleaned_bonuses = [line for line in bonuses if len(line) > 7]

    #print cleaned_tossups

    final_tossups, tu_errors = tossups_structured(cleaned_tossups)
    final_bonuses, bs_errors = bonuses_structured(cleaned_bonuses)

    #print final_tossups

    for tossup in final_tossups:
        print tossup

    for bonus in final_bonuses:
        print bonus


def find_first_tossup (text):

    first_index = next((i for i in range(len(text)) if re.search(ansregex, text[i], re.I)), None)
    return first_index - 1


def find_first_bonus (text):
    first_index = next((i for i in range(len(text)) if re.search('^\[\w*\]|^\(\w*\)', text[i], re.I)), None)
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



        #print i, leadin_markers[i], b_index, leadin_markers[b_index]


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


class InvalidPacket(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 80 + '\n'
        s += 'There was a problem in packet {0}\n'.format(self.args[0])
        s += '*' * 80 + '\n'

        return s


class InvalidTossup(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 50 + '\n'
        s += 'Invalid tossup {0}!\n'.format(self.args[2])
        s += 'The problem is in field: {0}, which has value: {1}\n'.format(self.args[0], self.args[1])
        s += '*' * 50 + '\n'

        return s


class InvalidBonus(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 50 + '\n'
        s += 'Invalid bonus {0}!\n'.format(self.args[2])
        s += 'The problem is in field: {0}, which has value: {1}\n'.format(self.args[0], self.args[1])
        s += '*' * 50 + '\n'

        return s


class Bonus:

    def __init__(self, leadin='', parts=[], answers=[], values=[], number=''):
        self.leadin = leadin
        self.parts = parts
        self.answers = answers
        self.number = number
        self.values = values

    def add_part(self, part):
        self.parts.append(part)

    def add_answer(self, answer):
        self.answers.append(answer)

    def to_json(self):
        return json.dumps({'leadin': self.leadin,
                           'parts': self.parts,
                           'answers': self.answers,
                           'number': self.number,
                           'values': self.values}) + '\n'

    def to_latex(self):
        leadin = self.leadin.replace('&ldquo;', '``')
        leadin = leadin.replace('&rdquo;', "''")
        leadin = leadin.replace('<i>', r'{\it ')
        leadin = leadin.replace('</i>', '}')
        leadin = r'\begin{{bonus}}{{{0}}}'.format(leadin) + '\n'
        parts = ''
        for val, part, answer in zip(self.values, self.parts, self.answers):
            answer = answer.replace('<req>', r'\ans{')
            answer = answer.replace('</req>', '}')
            answer = answer.replace('<b>', r'\ans{')
            answer = answer.replace('</b>', '}')
            answer = answer.replace('&ldquo;', '``')
            answer = answer.replace('&rdquo;', "''")
            part = part.replace('<i>', r'{\it ')
            part = part.replace('</i>', '}')
            part = part.replace('&ldquo;', '``')
            part = part.replace('&rdquo;', "''")

            parts += r'\bonuspart{{{0}}}{{{1}}}{{{2}}}'.format(val, part, answer) + '\n'
        return leadin + parts + r'\end{bonus}' + '\n'

    def is_valid(self):

        self.valid = False

        if self.leadin == '':
            raise InvalidBonus('leadin', self.leadin, self.number)
        if self.parts == []:
            raise InvalidBonus('parts', self.parts, self.number)
        if self.answers == []:
            raise InvalidBonus('answers', self.answers, self.number)
        if self.values == []:
            raise InvalidBonus('values', self.values, self.number)

        # for ans in self.answers:
        #    if re.match('answer:', ans) is None:
        #        raise InvalidBonus('answers', self.answers)
        #    if ans == '':
        #        raise Invalidbonus('answers', self.answers)

        for part in self.parts:
            if part == '':
                raise InvalidBonus('parts', self.parts, self.number)

        for val in self.values:
            if val == '':
                raise InvalidBonus('values', self.values, self.number)
            try:
                int(val)
            except ValueError:
                raise InvalidBonus('values', self.values, self.number)

        self.valid = True
        return True

    def __str__(self):

        s = '*' * 50 + '\n'
        s += self.leadin + '\n'

        for p, v, a in zip(self.parts, self.values, self.answers):
            s += '[{0}] {1}\nANSWER: {2}\n'.format(v, p, a)

        s += '*' * 50 + '\n'

        return s

class Tossup:
    def __init__(self, question='', answer='', number=''):
        self.question = question
        self.answer = answer
        self.number = number

    def to_json(self):
        return json.dumps({'question': self.question,
                           'answer': self.answer,
                           'number': self.number}) + '\n'

    def to_latex(self):
        answer = self.answer.replace('<req>', r'\ans{')
        answer = answer.replace('</req>', '}')
        answer = answer.replace('<b>', r'\ans{')
        answer = answer.replace('</b>', '}')
        question = self.question.replace('<i>', r'{\it ')
        question = question.replace('</i>', '}')
        answer = answer.replace('&ldquo;', '``')
        answer = answer.replace('&rdquo;', "''")
        question = question.replace('&ldquo;', '``')
        question = question.replace('&rdquo;', "''")

        return r'\tossup{{{0}}}{{{1}}}'.format(question, answer) + '\n'

    def is_valid(self):

        self.valid = False

        if self.question == '':
            raise InvalidTossup('question', self.question, self.number)

        if self.answer == '':
            raise InvalidTossup('answer', self.answer, self.number)

        # if re.match('answer:', self.answer) is None:
        #        raise InvalidTossup('answer', self.answer)

        self.valid = True
        return True

    def __str__(self):

        s = '*' * 50 + '\n'
        s += '{0}\nANSWER: {1}\n'.format(self.question, self.answer)
        s += '*' * 50 + '\n'

        return s