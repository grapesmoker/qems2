from __future__ import unicode_literals

from bs4 import BeautifulSoup
from django.utils.encoding import smart_unicode

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

def get_formatted_question_html(line, allowUnderlines, allowParens, allowNewLines):
    italicsFlag = False
    parensFlag = False
    underlineFlag = False
    output = ""
    for c in line:
        if (c == "~"):
            if (not italicsFlag):
                output += "<i>"
                italicsFlag = True
            else:
                output += "</i>"
                italicsFlag = False
        elif (c == "(" and allowParens):
            output += "<strong>("
            parensFlag = True
        elif (c == ")" and allowParens):
            output += ")</strong>"
            parensFlag = False
        else:
            if (c == "_" and allowUnderlines):
                if (not underlineFlag):
                    output += "<b><u>"
                    underlineFlag = True
                else:
                    output += "</u></b>"
                    underlineFlag = False
            else:
                output += c

    if (italicsFlag):
        output += "</i>"

    if (underlineFlag):
        output += "</u></b>"

    if (parensFlag):
        output += "</strong>"

    if (allowNewLines):
        output = output.replace("&lt;br&gt;", "<br />")

    return output

def get_character_count(line):
    count = 0
    parensFlag = False # Parentheses indicate pronunciation guide
    for c in line:
        if (parensFlag):
            if (c == ")"):
                parensFlag = False
        else:
            if (c == "("):
                parensFlag = True
            elif (c != "~"):
                count = count + 1 # Only count non-special chars not in pronunciation guide
                
    return count

def are_special_characters_balanced(line):
    underlineFlag = False
    italicsFlag = False
    parensFlag = False
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
        elif (c == '('):
            if (parensFlag):
                # There are too many open parens
                return False
            else:
                parensFlag = True
        elif (c == ')'):
            if (parensFlag):
                parensFlag = False
            else:
                # There are too many close parens
                return False
    
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
        
def get_bonus_type_from_question_type(question_type):
    if (question_type is None or str(question_type) == ''):
        print "bonus type none"
        return ACF_STYLE_BONUS
    elif (str(question_type) == VHSL_BONUS):
        print "vhsl"
        return VHSL_BONUS
    else:
        print "acf"
        return ACF_STYLE_BONUS        

def get_tossup_type_from_question_type(question_type):
    if (question_type is None or str(question_type) == ''):
        print "tossup type none"
        return ACF_STYLE_TOSSUP
    else:
        return ACF_STYLE_TOSSUP        
    
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
