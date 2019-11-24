from __future__ import unicode_literals

from bs4 import BeautifulSoup
from django.utils.encoding import smart_unicode
from django.utils.safestring import mark_safe
import unicodedata

DEFAULT_ALLOWED_TAGS = ['b', 'i', 'u', 'strong', 'em']

# translation mapping table that converts
# single smart quote characters to standard
# single quotes
SINGLE_QUOTE_MAP = {
        0x2018: 39,
        0x2019: 39,
        0x201A: 39,
        0x201B: 39,
        0x2039: 39,
        0x203A: 39,
}

# translation mapping table that converts
# double smart quote characters to standard
# double quotes
DOUBLE_QUOTE_MAP = {
        0x00AB: 34,
        0x00BB: 34,
        0x201C: 34,
        0x201D: 34,
        0x201E: 34,
        0x201F: 34,
}

# Constants for question types
ACF_STYLE_TOSSUP = 'ACF-style tossup'
ACF_STYLE_BONUS = 'ACF-style bonus'
VHSL_BONUS = 'VHSL bonus'

# Constants for edit types
QUESTION_CREATE = 'Question Create'
QUESTION_CHANGE = 'Question Change'
QUESTION_EDIT = 'Question Edit'
QUESTION_RESTORE = 'Question Restore'

# Constants for types of categories
CATEGORY = "Category"
SUB_CATEGORY = "Subcategory"
SUB_SUB_CATEGORY = "Subsubcategory"

# Constants for Packet types
ACF_PACKET = "ACF Packet"
VHSL_PACKET = "VHSL Packet"

# Constants for PeriodWideEntry types
ACF_REGULAR_PERIOD = "ACF Regular Period"
ACF_TIEBREAKER_PERIOD = "ACF Tiebreaker Period"
VHSL_TOSSUP_PERIOD = "VHSL Tossup Period"
VHSL_BONUS_PERIOD = "VHSL Bonus Period"
VHSL_TIEBREAKER_PERIOD = "VHSL Tiebreaker Period"

def remove_new_lines(line):
    return line.replace("\n", "").replace("\r", "")

def sanitize_html(html, allowed_tags=DEFAULT_ALLOWED_TAGS):
    soup = BeautifulSoup(html)
    for tag in soup.find_all(True):
        if tag.name == 'span':
            new_tag = None
            try:
                if tag['style'].find('text-decoration: underline') > -1:
                    new_tag = soup.new_tag('u')
                elif tag['style'].find('text-decoration: italic') > -1:
                    new_tag = soup.new_tag('em')

                if new_tag is not None:
                    new_tag.contents = tag.contents
                    tag.replace_with(new_tag)
            except KeyError as ex:
                pass
        elif tag.name not in allowed_tags:
            tag.hidden = True

    return soup.renderContents()

def strip_markup(html):
    html = convert_smart_quotes(html)
    html = html.replace("&", "&amp;")
    soup = BeautifulSoup(html)
    return soup.get_text()

def html_to_latex(html, replacement_dict):
    # replace the html tags with the appropriate latex markup
    # dict takes the form {'tag': 'latex_command'}, e.g. applying
    # {'b': 'bf'} to <b>answer</b> will produce \bf{answer}

    for h, l in replacement_dict.items():
        open_tag = '<{0}>'.format(h)
        close_tag = '</{0}>'.format(h)
        start_cmd = r'''\{0}{{'''.format(l)
        end_cmd = '}'
        html = html.replace(open_tag, start_cmd)
        html = html.replace(close_tag, end_cmd)

    return html

def get_answer_no_formatting(line):
    output = line
    output = strip_markup(output)
    output = output.replace('_', '')
    output = output.replace('~', '')
    return output

# Figure out if there's an "["
def get_primary_answer(line):
    if line is None:
        return line
    
    index = line.lower().find("[")
    if (index >= 0):
        return line[:index]
    else:
        return line

def preview(text):
    if (text is None):
        return text
    
    if (len(text) > 81):
        return mark_safe(text[0:81] + '...')
    else:
        return mark_safe(text)    

def get_formatted_question_html_for_bonus_answers(bonus):
    return get_formatted_question_html(bonus.part1_answer[0:80], True, True, False, False) + '<br />' + get_formatted_question_html(bonus.part2_answer[0:80], True, True, False, False) + '<br />' + get_formatted_question_html(bonus.part3_answer[0:80], True, True, False, False) + '<br />'

def get_formatted_question_html(line, allowUnderlines, allowParens, allowNewLines, allowPowers):
    italicsFlag = False
    parensFlag = False
    underlineFlag = False
    needToRestoreItalicsFlag = False
    subScriptFlag = False
    superScriptFlag = False
    powerFlag = False
    powerIndex = -1
    promptFlag = False
    index = 0
    
    previousChar = u""
    secondPreviousChar = u""
    output = u""
    nextChar = u""
    
    # If powers are allowed, see if there's a power in this question
    # If so, then start the question in power
    if (allowPowers):        
        powerIndex = line.find(u"(*)")
        if (powerIndex > -1):
            powerFlag = True
            output += u"<strong>"
                
    while (index < len(line)):
        c = line[index]        
        if (index < len(line) - 1):
            nextChar = line[index + 1]
        else:
            nextChar = ""
        
        if (index >= powerIndex and powerFlag):
            powerFlag = False
            output += u"(*)</strong>"
            index += 3 # Skip over the rest of what's in the power mark
            continue
        
        if (c == u"~"):
            if (not italicsFlag):
                output += u"<i>"
                italicsFlag = True
            else:
                output += u"</i>"
                italicsFlag = False
        elif (c == u"(" and allowParens and previousChar != u"\\"):
            if (italicsFlag):
                needToRestoreItalicsFlag = True
                itatlicsFlag = False
                output += u"</i>"
            
            if (not powerFlag):
                output += u"<strong>("
                parensFlag = True
            else:
                output += u"("
        elif (c == u"(" and allowParens and previousChar == u"\\" and secondPreviousChar != u"\\"):
            output = output[:-1] # Get rid of the escape character
            output += c
        elif (c == u")" and allowParens and previousChar != u"\\" and secondPreviousChar != u"\\"):
            if (not powerFlag):
                output += u")</strong>"
                parensFlag = False
            else:
                output += u")"

            if (needToRestoreItalicsFlag):
                output += u"<i>"
                italticsFlag = True
                needToRestoreItalicsFlag = False

        elif (c == u")" and allowParens and previousChar == u"\\"):
            output = output[:-1] # Get rid of the escape character
            output += c
        elif (c == u"s" and previousChar == u"\\" and secondPreviousChar != u"\\" and not superScriptFlag):
            output = output[:-1] # Get rid of the escape character
            if (subScriptFlag):
                subScriptFlag = False
                output += u"</sub>"
            else:
                subScriptFlag = True
                output += u"<sub>"
        elif (c == u"S" and previousChar == u"\\" and secondPreviousChar != u"\\" and not subScriptFlag):
            output = output[:-1] # Get rid of the escape character
            if (superScriptFlag):
                superScriptFlag = False
                output += u"</sup>"
            else:
                superScriptFlag = True
                output += u"<sup>"
        else:
            if (c == u"_" and allowUnderlines):
                if (nextChar == u"_"):
                    # This is a prompt
                    if (not promptFlag):
                        output += u"<u>"
                        promptFlag = True
                    else:
                        output += u"</u>"
                        promptFlag = False
                    
                    index += 1 # Skip ahead so we don't re-process this character
                else:
                    # This is a regular answer line
                    if (not underlineFlag):
                        output += u"<u><b>"
                        underlineFlag = True
                    else:
                        output += u"</b></u>"
                        underlineFlag = False
            else:
                output += c
        secondPreviousChar = previousChar
        previousChar = c
        index += 1

    if (italicsFlag):
        output += u"</i>"

    if (underlineFlag):
        output += u"</b></u>"

    if (parensFlag):
        output += u"</strong>"
        
    if (powerFlag):
        output += u"</strong>"
        
    if (promptFlag):
        output += u"</u>"

    if (allowNewLines):
        output = output.replace(u"&lt;br&gt;", u"<br />")

    return output

def get_character_count(line, ignore_pronunciation):
    if not ignore_pronunciation:
        return len(line)

    count = 0
    parensFlag = False # Parentheses indicate pronunciation guide
    previousChar = ""
    for c in line:
        if (parensFlag):
            if (c == ")" and previousChar != "\\"):
                parensFlag = False
        else:
            if (c == "(" and previousChar != "\\"):
                parensFlag = True                    
            elif (c != "~" and not (previousChar == "\\" and (c == ")" or c == "("))):
                count = count + 1 # Only count non-special chars not in pronunciation guide
        previousChar = c

    return count

def are_special_characters_balanced(line):
    underlineFlag = False
    italicsFlag = False
    parensFlag = False
    previousChar = ""
    for c in line:
        if (c == '_'):
            if (underlineFlag):
                underlineFlag = False
            else:
                underlineFlag = True
        elif (c == '~'):
            if (italicsFlag):
                italicsFlag = False
            else:
                italicsFlag = True
        elif (c == '(' and previousChar != "\\"):
            if (parensFlag):
                # There are too many open parens
                return False
            else:
                parensFlag = True
        elif (c == ')' and previousChar != "\\"):
            if (parensFlag):
                parensFlag = False
            else:
                # There are too many close parens
                return False
        previousChar = c

    if (underlineFlag or italicsFlag or parensFlag):
        return False
    else:
        return True

def does_answerline_have_underlines(line):
    if (line == ""):
        return True # Ignore completely blank lines

    if (line.find("_") == -1):
        return False
    else:
        return True

def convert_smart_quotes(line):
    return smart_unicode(line).translate(DOUBLE_QUOTE_MAP).translate(SINGLE_QUOTE_MAP)

def strip_special_chars(line):
    return line.replace('_', '').replace('~', '')

def strip_unicode(line):
    if (isinstance(line, str)):
        # line is not a unicode string, and normalizing it will throw
        return line
    if (line is None or line == ""):
        return ""
    return ''.join(c for c in unicodedata.normalize('NFKD', line)
              if unicodedata.category(c) != 'Mn')

def get_bonus_type_from_question_type(question_type):
    if (question_type is None or str(question_type) == ''):
        # print "bonus type none"
        return ACF_STYLE_BONUS
    elif (str(question_type) == VHSL_BONUS):
        # print "vhsl"
        return VHSL_BONUS
    else:
        # print "acf"
        return ACF_STYLE_BONUS

def get_tossup_type_from_question_type(question_type):
    if (question_type is None or str(question_type) == ''):
        # print "tossup type none"
        return ACF_STYLE_TOSSUP
    else:
        return ACF_STYLE_TOSSUP

def strip_answer_from_answer_line(line):
    if (line is not None):
        line = line.replace("ANSWER: ", "")
    
    return line

class InvalidTossup(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 50 + '<br />'
        s += 'Invalid tossup {0}!<br />'.format(self.args[2])
        s += 'The problem is in field: {0}, which has value: {1}<br />'.format(self.args[0], self.args[1])
        s += '*' * 50 + '<br />'

        return s


class InvalidBonus(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 50 + '<br />'
        s += 'Invalid bonus {0}!<br />'.format(self.args[2])
        s += 'The problem is in field: {0}, which has value: {1}<br />'.format(self.args[0], self.args[1])
        s += '*' * 50 + '<br />'

        return s

class InvalidPacket(Exception):

    def __init__(self, *args):
        self.args = [a for a in args]

    def __str__(self):
        s = '*' * 80 + '\n'
        s += 'There was a problem in packet {0}\n'.format(self.args[0])
        s += '*' * 80 + '\n'

        return s
