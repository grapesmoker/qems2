from registration.signals import user_registered
from django.dispatch import receiver
from qems2.qsub.forms import *
from qems2.qsub.models import *
from django.db.models.signals import post_save
from django_comments.models import Comment
from django.contrib.sites.models import get_current_site
from sets import Set
from django.core.mail import send_mail

@receiver(post_save)
def email_on_comments(sender, instance, created, raw, using, update_fields, **kwargs):
    try:
        if (type(instance) is Comment):        
            # Figure out if this is a tossup or bonus we've added a comment for
            print "New comment has been saved"        
            mail_set = Set()
            target = instance.content_object
            if (type(target) is Tossup or type(target) is Bonus):
                author = target.author
                if (author.send_mail_on_comments):
                    mail_set.add(author.user.email)
                
                # Get all people on this thread
                for comment in Comment.objects.filter(object_pk=target.id).filter(content_type_id=instance.content_type_id):
                    # Need to figure out writer from user
                    comment_writer = comment.user.writer
                    if (comment_writer.send_mail_on_comments):
                        mail_set.add(comment.user.email)
            
                # Since you don't want to get an e-mail if you made your own comment, delete yoursel from the set
                if (instance.user.email in mail_set):
                    mail_set.remove(instance.user.email)
                
                if (len(mail_set) > 0):
                    subject = "New QEMS2 comment for " + str(target)
                    qset = str(target.question_set)
                    if (type(target) is Tossup):
                        url = ''.join(['http://', get_current_site(None).domain, '/edit_tossup/', str(target.id)])
                        
                    else:
                        url = ''.join(['http://', get_current_site(None).domain, '/edit_bonus/', str(target.id)])
                        
                    body = 'The question on "{0!s}" for the set "{1!s}" has a new comment by {2!s}:\n\n{3!s}\n\nView the question at {4!s}.\n\nTo opt out of these e-mails, change the settings in your profile.'.format(
                        str(target),
                        qset,
                        str(instance.user),
                        instance.comment,
                        url)
                        
                    send_mail(subject, body, "QEMS2", mail_set)
    except:
        print "Error sending mail for comments"
                    
# Called when a user is created, saves first and last name info
@receiver(user_registered)
def user_created(sender, user, request, **kwargs):
    form = RegistrationFormWithName(request.POST)    
    user.first_name=form.data['first_name']
    user.last_name=form.data['last_name']
    user.save()
