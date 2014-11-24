from __future__ import unicode_literals

from bs4 import BeautifulSoup

DEFAULT_ALLOWED_TAGS = ['b', 'i', 'u', 'strong', 'em']

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
                    output += "</b></u>"
                    underlineFlag = False
            else:
                output += c
    
    if (italicsFlag):
        output += "</i>"
        
    if (underlineFlag):
        output += "</b></u>"
    
    if (parensFlag):
        output += "</strong>"
    
    if (allowNewLines):
        output = output.replace("&lt;br&gt;", "<br>")
            
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
