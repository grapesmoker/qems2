from registration.signals import user_registered
from django.dispatch import receiver
from qems2.qsub.forms import *
from qems2.qsub.models import *
from django.db.models.signals import post_save
from django_comments.models import Comment
from django.contrib.sites.models import get_current_site
from sets import Set
from django.core.mail import send_mail
from django.db.models import Q
import sys

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
                
                # Figure out if someone has signed up to receive all comment notifications
                # TODO: Probably add some error handling since these settings don't exist for everyone
                # TODO: Add a script to fix the above thing
                all_writers = Writer.objects.filter(Q(question_set_writer=target.question_set) | Q(question_set_editor=target.question_set)).distinct().order_by('user__last_name', 'user__first_name', 'user__username')
                for writer in all_writers:
                    set_settings = WriterQuestionSetSettings.objects.get(writer=writer, question_set=target.question_set)
                    if (set_settings.email_on_all_new_comments):
                        mail_set.add(writer.user.email)
                        
                    # Figure out if they've signed up for this category
                    category_settings = PerCategoryWriterSettings.objects.get(writer_question_set_settings=set_settings, distribution_entry=target.category)
                    if (category_settings.email_on_new_comments):
                        mail_set.add(writer.user.email)
                
                # Since you don't want to get an e-mail if you made your own comment, delete yoursel from the set
                if (instance.user.email in mail_set):
                    mail_set.remove(instance.user.email)
                
                if (len(mail_set) > 0):
                    qset = str(target.question_set)
                    subject = "New QEMS2 comment for " + str(target) + " in set " + qset
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

                    print "Email list to send for new comment: ", str(email_list)
                    print "Email details", subject, body                 
                    send_mail(subject, body, settings.EMAIL_HOST_USER, mail_set, fail_silently=False)
                    print "Sent new comment mail to: " + str(mail_set)   
    except:
        print "Error sending mail for comments:", sys.exc_info()[0]

@receiver(post_save)
def email_on_new_questions(sender, instance, created, raw, using, update_fields, **kwargs):
    try:
        # Only care about new questions
        if (created):
            if (type(instance) is Tossup or type(instance) is Bonus):        
                print "New tossup or bonus.  Checking for who to send e-mails to."
                
                # Go through each person in this set and see their options
                all_writers = Writer.objects.filter(Q(question_set_writer=instance.question_set) | Q(question_set_editor=instance.question_set)).distinct().order_by('user__last_name', 'user__first_name', 'user__username')
                email_list = []
                for writer in all_writers:
                    try:
                        if (writer != instance.author or writer.user.username == "bentley"): # TODO: Remove this hard-coded reference to bentley once done debugging
                            set_settings = WriterQuestionSetSettings.objects.get(writer=writer, question_set=instance.question_set)
                            if (set_settings.email_on_all_new_questions):
                                print "Matched all"
                                email_list.append(writer.user.email)
                            else:
                                category_settings = PerCategoryWriterSettings.objects.get(writer_question_set_settings=set_settings, distribution_entry=instance.category)
                                if (category_settings.email_on_new_questions):
                                    print "Matched on category: " + str(category_settings.distribution_entry)
                                    email_list.append(writer.user.email)
                    except:
                        print "Error getting settings for writer: " + str(writer)
                
                if (len(email_list) > 0):
                    qset = str(instance.question_set)
                    subject = "New QEMS2 question for " + str(instance) + " in set " + qset
                    if (type(instance) is Tossup):
                        url = ''.join(['http://', get_current_site(None).domain, '/edit_tossup/', str(instance.id)])
                        
                    else:
                        url = ''.join(['http://', get_current_site(None).domain, '/edit_bonus/', str(instance.id)])
                        
                    body = '{0!s} has written a new question on for the set {1!s}:\n\n{2!s}\n\nView the question at {3!s}.\n\nTo opt out of these e-mails, change the settings in your profile.'.format(
                        str(instance.author),
                        qset,
                        instance.to_plain_text(),
                        url)
                    
                    print "Email list to send for new question: ", str(email_list)
                    print "Email details", subject, body
                    send_mail(subject, body, settings.EMAIL_HOST_USER, email_list, fail_silently=False)
                    print "Sent new question mail to: " + str(email_list)       
    except:
        print "Error sending mail for new question", sys.exc_info()[0]

# Called when a user is created, saves first and last name info
@receiver(user_registered)
def user_created(sender, user, request, **kwargs):
    form = RegistrationFormWithName(request.POST)    
    user.first_name=form.data['first_name']
    user.last_name=form.data['last_name']
    user.save()
