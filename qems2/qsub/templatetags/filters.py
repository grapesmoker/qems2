from django.template.defaultfilters import register
from django.utils.datastructures import SortedDict
from django.utils.safestring import mark_safe
from qems2.qsub.models import *
from qems2.qsub.utils import sanitize_html, strip_markup, get_formatted_question_html, get_answer_no_formatting
from django.contrib.contenttypes.models import ContentType
from django.contrib.comments import *

@register.filter(name='lookup')
def lookup(dict, key):
    if key in dict:
        return dict[key]
    else:
        return 0

@register.filter(name='tossup_or_bonus')
def tossup_or_bonus(type):
    return str(type)

@register.filter(name='tossups_or_bonuses')
def tossups_or_bonuses(type):
    if type == 'tossup':
        return 'tossups'
    if type == 'bonus':
        return 'bonuses'
    return type

@register.filter(name='get_editor_categories')
def get_editor_categories(editor, tour):

    if Role.objects.filter(player=editor, tournament=tour).exists():
        role = Role.objects.get(player=editor, tournament=tour)
        categories = role.category.split(';')

        cat_list = [cat_tuple[1] for cat_tuple in CATEGORIES if cat_tuple[0] in categories]
    else:
        cat_list = []

    return mark_safe('<p>' + '<br>'.join(cat_list) + '</p>')

@register.filter(name='preview')
def preview(text):
    if (len(text) > 81):
        return mark_safe(text[0:81] + '...')
    else:
        return mark_safe(text)

@register.filter(name='short_preview')
def short_preview(text):
    return mark_safe(text[0:25])

@register.filter(name='bonus_answers')
def bonus_answers(bonus):
    return mark_safe(answer_html(bonus.part1_answer[0:80].encode('utf-8')) + '<br />'
    + answer_html(bonus.part2_answer[0:80].encode('utf-8')) + '<br />'
    + answer_html(bonus.part3_answer[0:80].encode('utf-8')))

@register.filter(name='percent')
def percent(x, y):
    try:
        if float(y) != 0:
            val = 100 * float(x) / float(y)
            if (val > 100):
                val = 100
            return '{0:0.1f}%'.format(val)
        else:
            return None
    except Exception as ex:
        return None

@register.filter(name='fpercent')
def fpercent(x, y):
    try:
        if float(y) != 0:
            return 100 * float(x) / float(y)
        else:
            return None
    except Exception as ex:
        return None

@register.filter(name='tossups_remaining')
def tossups_remaining(entry):
    val = entry['tu_req'] - entry['tu_in_cat']
    if (val < 0):
        val = "0 (" + str((val * -1)) + " extra)"
        return val
    else:
        return val

@register.filter(name='bonuses_remaining')
def bonuses_remaining(entry):
    val = entry['bs_req'] - entry['bs_in_cat']
    if (val < 0):
        val = "0 (" + str((val * -1)) + " extra)"
        return val
    else:
        return val

@register.filter(name='overall_percent')
def overall_percent(entry):
    tu_in_cat = entry['tu_in_cat']
    bs_in_cat = entry['bs_in_cat']
    tu_req = entry['tu_req']
    bs_req = entry['bs_req']
    if (tu_in_cat is None):
        tu_in_cat = 0
    if (bs_in_cat is None):
        bs_in_cat = 0
    if (tu_req is None):
        tu_req = 0
    if (bs_req is None):
        bs_req = 0

    percentage = fpercent(tu_in_cat + bs_in_cat, tu_req + bs_req)
    if percentage == None:
        return mark_safe('<i class="fa fa-check"></i> ' + str(percentage))
    elif percentage >= 100:
        return mark_safe('<i class="fa fa-check"></i> ' + '{0:0.2f}%'.format(percentage))
    else:
        return mark_safe('<i class="fa fa-times"></i> ' + '{0:0.2f}%'.format(percentage))

@register.filter(name='check_mark_if_100_pct')
def check_mark_if_100_pct(x, y):
    percentage = fpercent(x, y)
    if percentage >= 100 or percentage == None:
        return mark_safe('<i class="fa fa-check"></i>')
    else:
        return mark_safe('<i class="fa fa-times"></i>')

@register.filter(name='class_name')
def class_name(obj):
    return obj.__class__.__name__

@register.filter(name='sort')
def listsort(value):
    if isinstance(value, dict):
        print "Sorted dict called"
        new_dict = SortedDict()
        key_list = sorted(value.keys())
        for key in key_list:
            new_dict[key] = value[key]
        return new_dict
    elif isinstance(value, list):
        print "List called"
        return sorted(value)
    else:
        print "Other called"
        return value
    listsort.is_safe = True

@register.filter(name='question_html')
def question_html(line):
    return get_formatted_question_html(line, False, True, False)

@register.filter(name='answer_html')
def answer_html(line):
    return get_formatted_question_html(line, True, True, False)

@register.filter(name='answer_no_formatting')
def answer_no_formatting(line):
    return get_answer_no_formatting(line)

@register.filter(name='comment_html')
def comment_html(comment):
    return get_formatted_question_html(comment, True, False, True)

@register.filter(name='tossup_html')
def tossup_html(tossup):
    return tossup.to_html()

@register.filter(name='tossup_html_verbose')
def tossup_html_verbose(tossup):
    return tossup.to_html(include_category=True, include_character_count=True)

@register.filter(name='bonus_html')
def bonus_html(bonus):
    return bonus.to_html()

@register.filter(name='bonus_leadin')
def bonus_leadin(bonus):
    return preview(bonus.leadin_to_html())

@register.filter(name='bonus_html_verbose')
def bonus_html_verbose(bonus):
    return bonus.to_html(include_category=True, include_character_count=True)

@register.filter(name='tossup_history_html')
def tossup_history_html(tossup):
    return tossup.to_html()

@register.filter(name='bonus_history_html')
def bonus_history_html(bonus):
    return bonus.to_html()

@register.filter(name='tossup_last_comment_date')
def tossup_last_comment_date(tossup):
    tossup_content_type_id = ContentType.objects.get(name="tossup")
    comments = Comment.objects.filter(object_pk=tossup.id).filter(content_type_id=tossup_content_type_id).order_by('-id')
    if (len(comments) > 0):
        return comments[0].submit_date
    else:
        return ''

@register.filter(name='bonus_last_comment_date')
def bonus_last_comment_date(bonus):
    bonus_content_type_id = ContentType.objects.get(name="bonus")
    comments = Comment.objects.filter(object_pk=bonus.id).filter(content_type_id=bonus_content_type_id).order_by('-id')
    if (len(comments) > 0):
        return comments[0].submit_date
    else:
        return ''

#@register.filter(name='compare_categories'):
#def compare_categories(cat1, cat2):
