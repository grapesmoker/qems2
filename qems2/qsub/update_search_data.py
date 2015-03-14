from qems2.qsub.models import *
from qems2.qsub.utils import *

print "Updating search indexes for tossups"
tossups = Tossup.objects.all()
for tossup in tossups:
    tossup.setup_search_fields(remove_unicode=False)
    tossup.save()

print "Updating search indexes for bonuses"
bonuses = Bonus.objects.all()
for bonus in bonuses:
    bonus.setup_search_fields(remove_unicode=False)
    bonus.save()

