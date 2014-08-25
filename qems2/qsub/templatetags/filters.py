from django.template.defaultfilters import register
from django.utils.safestring import mark_safe
from qems2.qsub.models import *

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
    return mark_safe(text[0:81] + '...')

@register.filter(name='bonus_answers')
def bonus_answers(bonus):
    return mark_safe(bonus.part1_answer[0:80] + '<br>'
    + bonus.part2_answer[0:80] + '<br>'
    + bonus.part3_answer[0:80] + '<br>')

@register.filter(name='percent')
def percent(x, y):
    print x, y
    print type(x), type(y)
    try:
        if float(y) != 0:
            return str(100 * float(x) / float(y))
        else:
            return None
    except Exception as ex:
        return None