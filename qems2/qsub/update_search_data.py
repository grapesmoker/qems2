from qems2.qsub.models import *
from qems2.qsub.utils import *
from django.db import transaction

@transaction.commit_manually
def update_search_data():
    print "Updating search indexes for tossups"
    tossups = Tossup.objects.all()
    count = 1

    for tossup in tossups:
        tossup.setup_search_fields()
        tossup.save()
        print "Saved tossup " + str(count) + " of " + str(len(tossups))
        count += 1

    count = 1
    print "Updating search indexes for bonuses"
    bonuses = Bonus.objects.all()
    for bonus in bonuses:
        bonus.setup_search_fields()
        bonus.save()
        print "Saved bonus " + str(count) + " of " + str(len(bonuses))
        count += 1

    print "Committing"
    transaction.commit()
    print "Finished commit"

update_search_data()
