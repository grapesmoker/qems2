__author__ = 'jerry'

import re
import json
import string

from qems2.qsub.models import *
from qems2.qsub.utils import *
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
                tossup = create_tossup(tossup_text, tossup_answer, tossup_category)
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
                
            bonus = create_bonus(leadin, parts, answers, values, question_type_text=ACF_STYLE_BONUS, category_text=category)            
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
            
            bonus = create_bonus('', [question], [answer], [], question_type_text=VHSL_BONUS, category_text=category)
            try:
                bonus.is_valid()
                bonuses.append(bonus)
            except InvalidBonus as ex:
                print ex
                bonus_errors.append(bonus)
            vhsl_bonus_flag = False
 
    return tossups, bonuses, tossup_errors, bonus_errors

def create_tossup(question='', answer='', category_text='', question_type_text='ACF-style tossup'):
    
    question = escape(question)
    answer = escape(remove_answer_label(answer))

    categories = DistributionEntry.objects.all() 
    setCategory = None
    for category in categories:
        formattedCategory = category.category + " - " + category.subcategory
        print "formattedCategory: " + formattedCategory
        if (formattedCategory == category_text):
            print "setCategory"
            setCategory = category
            break
    
    questionTypes = QuestionType.objects.all()
    setQuestionType = None
    for questionType in questionTypes:
        if (str(questionType) == question_type_text):
            setQuestionType = questionType
            break;
    
    tossup = Tossup(tossup_text=question, tossup_answer=answer, category=setCategory, question_type=setQuestionType)
    return tossup

def create_bonus(leadin='', parts=[], answers=[], values=[], question_type_text=ACF_STYLE_BONUS, category_text=''):
    
    leadin = escape(leadin)
    sanitizedParts = []
    for part in parts:
        sanitizedParts.append(escape(part))
    parts = sanitizedParts
    
    # For VHSL bonuses, make sure that we have enough data to pass into the bonus form
    while (len(parts) < 3):
        parts.append('')
    
    while (len(answers) < 3):
        answers.append('')
        
    # TODO: We don't do anything with values right now
    #sanitizedValues = []
    #for value in values:
    #    sanitizedValues.append(escape(value))        
    #values = sanitizedValues
    
    questionTypes = QuestionType.objects.all()
    setQuestionType = None
    for questionType in questionTypes:
        if (str(questionType) == question_type_text):
            print "setQuestionType: " + str(questionType)
            setQuestionType = questionType
            break;

    categories = DistributionEntry.objects.all() 
    setCategory = None
    for category in categories:
        formattedCategory = category.category + " - " + category.subcategory
        if (formattedCategory == category_text):
            setCategory = category
            break
    
    modifiedAnswers = []
    for answer in answers:
        formattedAnswer = escape(remove_answer_label(answer))
        modifiedAnswers.append(formattedAnswer)
    answers = modifiedAnswers
    
    bonus = Bonus(leadin=leadin, part1_text=parts[0], part1_answer=answers[0],
        part2_text=parts[1], part2_answer=answers[1], part3_text=parts[2],
        part3_answer=answers[2], category=setCategory, question_type=setQuestionType)
    return bonus
