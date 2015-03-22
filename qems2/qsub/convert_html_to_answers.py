# This script updates all tossups and bonuses in the NSC set to use
# ~ and _ rather than html tags

from qems2.qsub.models import *
from django.db import transaction


def convert_html(line):
    changed = False
    if ("<b>" in line or "<u>" in line or "<strong>" in line or "<i>" in line):
        line = line.replace("<u>", "_").replace("</u>", "_")
        line = line.replace("<strong>", "").replace("</strong>", "").replace("<b>", "").replace("</b>", "")
        line = line.replace("<i>", "~").replace("</i>", "~")
        changed = True
        
    return line, changed

#@transaction.commit_manually
def update_tossups_and_bonuses():
    print "Starting script to update PACE NSC formatting"

    qset = QuestionSet.objects.get(id=2)
    for tossup in Tossup.objects.filter(question_set=qset):        
        tossup.tossup_text, changed1 = convert_html(tossup.tossup_text)
        tossup.tossup_answer, changed2 = convert_html(tossup.tossup_answer)
        if (changed1 or changed2):
            print "saving tossup", tossup.id
            tossup.save()

    for bonus in Bonus.objects.filter(question_set=qset):
        bonus.leadin, changed1 = convert_html(bonus.leadin)
        bonus.part1_text, changed2 = convert_html(bonus.part1_text)
        bonus.part1_answer, changed3 = convert_html(bonus.part1_answer)
        bonus.part2_text, changed4 = convert_html(bonus.part2_text)
        bonus.part2_answer, changed5 = convert_html(bonus.part2_answer)
        bonus.part3_text, changed6 = convert_html(bonus.part3_text)
        bonus.part3_answer, changed7 = convert_html(bonus.part3_answer)
        
        if (changed1 or changed2 or changed3 or changed4 or changed5 or changed6 or changed7):
            print "saving bonus", bonus.id
            bonus.save()

    print "Committing"
    transaction.commit()

    print "Finished"

update_tossups_and_bonuses()
