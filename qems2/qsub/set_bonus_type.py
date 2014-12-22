# Makes sure that ACF bonuses and VHSL bonuses have their types set properly
from qems2.qsub.models import *
from qems2.qsub.utils import *

print "Starting script"

for bonus in Bonus.objects.all():
    if (is not None bonus.leadin and bonus.leadin != ''):
        bonus.question_type = QuestionType.objects.get(question_type=ACF_STYLE_BONUS)
    else:
        bonus.question_type = QuestionType.objects.get(question_type=VHSL_BONUS)        
    
    bonus.save()

print "Finished"
