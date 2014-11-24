__author__ = 'jerry'

import re
import json
import string

from qems2.qsub.model_utils import sanitize_html
from django.utils.html import escape

ansregex = '(?i)a..?wers?:\s*'
bpart_regex = '^\[\d+\]'
vhsl_bpart_regex = '^\[V\d+\]'
category_regex = '\{(.+)}'
bonus_value_regex = '\[|\]|\(|\)'

def is_answer(line):

    return re.search(ansregex, line) is not None

def is_bpart(line):
    
    return re.search(bpart_regex, line) is not None
    
def is_vhsl_bpart(line):
    
    return re.search(vhsl_bpart_regex, line) is not None

def is_category(line):
    
    return re.search(category_regex, line) is not None

def get_category(line):
    
    if (is_category(line)):
        return re.search(category_regex, line).group(1)
    else:
        return ''

def remove_category(line):
    
    return re.sub(category_regex, '', line)
    
def remove_answer_label(line):
    
    return re.sub(ansregex, '', line)

def get_bonus_part_value(line):
    
    match = re.search(bpart_regex, line)
    return re.sub(bonus_value_regex, '', match.group(0))     

def format_answerline_underscores(line):
    
    output = ''
    underlineFlag = False
    for c in line:
        if (c == '_'):
            if (underlineFlag):
                underlineFlag = False
                output = output + '</b></u>'
            else:
                underlineFlag = True
                output = output + '<b><u>'
        else:
            output = output + c
    
    # If we're at the end of the string and there isn't a closing flag, add it
    if (underlineFlag):
        output = output + '</b></u>'
    
    return output

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

def parse_packet_data(data):

    data = [line for line in data if line.strip() != '']

    tossups = []
    bonuses = []

    tossup_errors = []
    bonus_errors = []

    tossup_flag = False
    bonus_flag = False
    vhsl_bonus_flag = False
    
    question_stack = []

    for i in range(len(data)):

        this_line = data[i].strip()
        
        # push current line onto the stack
        question_stack.append(this_line)

        if not tossup_flag and not bonus_flag and not vhsl_bonus_flag:
            if is_answer(this_line):
                # if no flags have been set, and we encounter an ANSWER: then we
                # know that this is a tossup
                tossup_flag = True
            elif is_bpart(this_line):
                # if no flags have been set and we encounter a [10] then we
                # know that this is a bonus
                bonus_flag = True
            elif is_vhsl_bpart(this_line):
                # if not flags have been set and we encounter a [V10] then we
                # know that this is a VHSL bonus
                vhsl_bonus_flag = True

        print this_line
        print tossup_flag, bonus_flag, vhsl_bonus_flag

        # if there are two items on the stack and the second one is an ANSWER:
        # pop the stack and create a tossup
        if (len(question_stack) == 2 or i == len(data) - 1) and tossup_flag:
            if (len(question_stack) < 2):
                print "Tossups required both a question and answer, but only one item found on stack."
                tossup = Tossup('', question_stack.pop(), i, '')
                tossup_errors.append(tossup)
            else:
                tossup_answer = question_stack.pop()
                tossup_category = get_category(tossup_answer)
                tossup_answer = remove_category(tossup_answer)

                tossup_text = question_stack.pop()            
                tossup = Tossup(tossup_text, tossup_answer, i, tossup_category)
                try:
                    tossup.is_valid()
                    tossups.append(tossup)
                except InvalidTossup as ex:
                    print ex
                    tossup_errors.append(tossup)
                tossup_flag = False
            
        # if we are in bonus mode and the line is not an answer or a bonus part
        # then pop the stack until it's empty and form a bonus
        elif bonus_flag and ((not is_answer(this_line) and not is_bpart(this_line)) or i == len(data) - 1):
            
            # If there are still lines to read, the top of the stack represents the first line
            # in the next question.  Otherwise, it's the last part of the bonus and we don't
            # want to pop it
            next_question_line = ''
            if (i < len(data) - 1):
                next_question_line = question_stack.pop()
                
            parts = []
            values = []
            answers = []
            leadin = ''
            category = ''
            while question_stack != []:
                bonus_line = question_stack.pop()
                print "Bonus Line from question stack: " + bonus_line
                if is_bpart(bonus_line):
                    print "Is BPart"
                    val = get_bonus_part_value(bonus_line)
                    question = string.strip(re.sub(bpart_regex, '', bonus_line))
                    values.append(val)
                    parts.append(question)
                elif is_answer(bonus_line):
                    print "Is Answer"
                    answer = bonus_line
                    tempCategory = get_category(answer)
                    print "Answer Line: " + answer
                    print "TempCategory: " + tempCategory
                    if (tempCategory != ''):
                        category = tempCategory
                        answer = remove_category(answer)
                    
                    answers.append(answer)
                else:
                    print "Is Leadin"
                    leadin = bonus_line
            parts.reverse()
            values.reverse()
            answers.reverse()
            
            print leadin
            print parts
            print answers
            
            if (i < len(data) - 1):
                question_stack.append(next_question_line)
                
            bonus = Bonus(leadin, parts, answers, values, i, type="acf", category=category)            
            try:
                bonus.is_valid()
                bonuses.append(bonus)
            except InvalidBonus as ex:
                print ex
                bonus_errors.append(bonus)
            bonus_flag = False

        # special case for vhsl bonuses
        # There isn't a great way to tell VHSL bonuses from other bonuses, so need to require a special
        # bonus part flag of [V10] rahter than just [10]
        elif vhsl_bonus_flag and (is_answer(this_line) or i == len(data) - 1):
            answer = question_stack.pop()
            question = question_stack.pop()
            question = string.strip(re.sub(vhsl_bpart_regex, '', question))
            answer = string.strip(re.sub(ansregex, '', answer))
            category = get_category(answer)
            answer = remove_category(answer)
            
            bonus = Bonus('', [question], [answer], [], i, type='vhsl', category=category)
            try:
                bonus.is_valid()
                bonuses.append(bonus)
            except InvalidBonus as ex:
                print ex
                bonus_errors.append(bonus)
            vhsl_bonus_flag = False
 
    return tossups, bonuses, tossup_errors, bonus_errors

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
        s = '*' * 50 + '<br>'
        s += 'Invalid tossup {0}!<br>'.format(self.args[2])
        s += 'The problem is in field: {0}, which has value: {1}<br>'.format(self.args[0], self.args[1])
        s += '*' * 50 + '<br>'

        return s


class InvalidBonus(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 50 + '<br>'
        s += 'Invalid bonus {0}!<br>'.format(self.args[2])
        s += 'The problem is in field: {0}, which has value: {1}<br>'.format(self.args[0], self.args[1])
        s += '*' * 50 + '<br>'

        return s


class Bonus:

    def __init__(self, leadin='', parts=[], answers=[], values=[], number='', type='acf', category=''):
        self.leadin = escape(leadin)
        sanitizedParts = []
        for part in parts:
            sanitizedParts.append(escape(part))
        self.parts = sanitizedParts
        
        self.number = number
        
        sanitizedValues = []
        for value in values:
            sanitizedValues.append(escape(value))        
        self.values = sanitizedValues
        
        self.type = type
        self.category = escape(category)
        
        modifiedAnswers = []
        for answer in answers:
            formattedAnswer = escape(remove_answer_label(answer))
            modifiedAnswers.append(formattedAnswer)
        self.answers = modifiedAnswers

    def add_part(self, part):
        self.parts.append(part)

    def add_answer(self, answer):
        self.answers.append(answer)

    def to_json(self):
        return json.dumps({'leadin': self.leadin,
                           'parts': self.parts,
                           'answers': self.answers,
                           'number': self.number,
                           'values': self.values,
                           'type': self.type,                           
                           'category': self.category}) + '\n'

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

        if self.type == 'acf':

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

        elif self.type == 'vhsl':

            if self.parts == []:
                raise InvalidBonus('parts', self.parts, self.number)
            if self.answers == []:
                raise InvalidBonus('answers', self.answers, self.number)

            for part in self.parts:
                if part == '':
                    raise InvalidBonus('parts', self.parts, self.number)
                    
        else:
            raise InvalidBonus('type', self.type, self.number)

    def __str__(self):

        s = '*' * 50 + '\n'
        s += self.leadin + '\n'

        for p, v, a in zip(self.parts, self.values, self.answers):
            s += '[{0}] {1}\nANSWER: {2}\n'.format(v, p, a)

        s += '*' * 50 + '\n'

        return s

class Tossup:
    def __init__(self, question='', answer='', number='', category=''):
        self.question = escape(question)
        self.answer = escape(remove_answer_label(answer))
        self.number = number
        self.category = escape(category)

    def to_json(self):
        return json.dumps({'question': self.question,
                           'answer': self.answer,
                           'number': self.number,
                           'category': self.category}) + '\n'

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
