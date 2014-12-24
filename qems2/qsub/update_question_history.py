# This script updates existing tossups and bonuses with a value for question history

from qems2.qsub.models import *
from utils import *

print "Starting script"

for tossup in Tossup.objects.all():
    if (tossup.question_history is None):
        qh = QuestionHistory()
        qh.save()
        tosssup.question_history = qh
        tossup.save()
    
for bonus in Bonus.objects.all():
    if (bonus.question_history is None):
        qh = QuestionHistory()
        qh.save()
        bonus.question_history = qh
        bonus.save()

print "Finished"
