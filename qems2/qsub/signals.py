from registration.signals import user_registered
from django.dispatch import receiver
from qems2.qsub.forms import *

#@receiver(request_finished)
#def my_callback(sender, **kwargs):
#    print("Request finished - new function!")


# Called when a user is created, saves first and last name info
@receiver(user_registered)
def user_created(sender, user, request, **kwargs):
    form = RegistrationFormWithName(request.POST)
    user.first_name=form.data['first_name']
    user.last_name=form.data['last_name']
    user.save()
