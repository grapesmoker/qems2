from qems2.qsub.models import *

print "Starting script"

for user in User.objects.all():
    user.is_active = True
    user.save()
    
print "Finished script"
