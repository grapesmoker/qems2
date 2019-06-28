# This script creates standard question types, creates a 
# typical ACF distribution and adds some questions

from qems2.qsub.models import *
from qems2.qsub.utils import *
from datetime import datetime
from django.contrib.auth.models import User

# Create a new user
username = "admin2"
email = "qems2@pace-nsc.org"
password = "temp_password" # TODO: Change this
newUser = User.objects.create_user(username=username, email=email, password=password)

print "Starting script"

# Delete existing data
print "Deleting existing data"
for tossup in Tossup.objects.all():
    tossup.delete()

for bonus in Bonus.objects.all():
    bonus.delete()

for de in DistributionEntry.objects.all():
    de.delete()

for distribution in Distribution.objects.all():
    distribution.delete()

for question_type in QuestionType.objects.all():
    question_type.delete()

for question_set in QuestionSet.objects.all():
    question_set.delete()

for writer in Writer.objects.all():
    if (writer.user.username != username):
        writer.user.delete()
        writer.delete()

print "Creating data"

distribution = Distribution(name="Default Distribution")
distribution.save()

dist_entry = DistributionEntry(
                distribution=distribution,
                category="History",
                subcategory="European",
                min_tossups=2,
                min_bonuses=2,
                max_tossups=2,
                max_bonuses=2)
dist_entry.save()

dist_entry = DistributionEntry(
                distribution=distribution,
                category="History",
                subcategory="American",
                min_tossups=1,
                min_bonuses=1,
                max_tossups=1,
                max_bonuses=1)
dist_entry.save()

dist_entry = DistributionEntry(
                distribution=distribution,
                category="History",
                subcategory="World",
                min_tossups=1,
                min_bonuses=1,
                max_tossups=1,
                max_bonuses=1)
dist_entry.save()

dist_entry = DistributionEntry(
                distribution=distribution,
                category="Arts",
                subcategory="Painting",
                min_tossups=1,
                min_bonuses=1,
                max_tossups=1,
                max_bonuses=1)
dist_entry.save()

dist_entry = DistributionEntry(
                distribution=distribution,
                category="Arts",
                subcategory="Classical Music",
                min_tossups=1,
                min_bonuses=1,
                max_tossups=1,
                max_bonuses=1)
dist_entry.save()

print "creating question types"

acf_style_tossup = QuestionType(question_type=ACF_STYLE_TOSSUP)
acf_style_tossup.save()

acf_style_bonus = QuestionType(question_type=ACF_STYLE_BONUS)
acf_style_bonus.save()

vhsl_bonus = QuestionType(question_type=VHSL_BONUS)
vhsl_bonus.save()

print "creating users"

#user = User.objects.get(username=username)
writer = Writer.objects.get(user=newUser)

qset = QuestionSet(
                    name="Default Question Set",
                    date=datetime.today(),
                    host="Default Host",
                    address="Foo",
                    owner=writer,
                    distribution=distribution,
                    num_packets=10)
qset.save()

print "Adding writer permissions"

writer.question_set_editor.add(qset)
writer.save()

print "Creating distribution entries"

for dist_entry in DistributionEntry.objects.filter(distribution=distribution):
    swde = SetWideDistributionEntry(
                                    question_set=qset,
                                    dist_entry=dist_entry,
                                    num_tossups=(10*dist_entry.max_tossups),
                                    num_bonuses=(10*dist_entry.max_bonuses))
    swde.save()

print "Creating tossups and bonuses"

tossup = Tossup(
                    question_set=qset,
                    tossup_text="Test ~tossup 1~.",
                    tossup_answer="test _answer 1_",
                    author=writer,
                    question_type=acf_style_tossup)
tossup.save_question(QUESTION_CREATE, writer)
                    
tossup = Tossup(
                    question_set=qset,
                    tossup_text="Test ~tossup 2~.",
                    tossup_answer="test _answer 2_",
                    author=writer,
                    question_type=acf_style_tossup)
tossup.save_question(QUESTION_CREATE, writer)               

bonus = Bonus(
                    question_set=qset,
                    leadin="Test leadin for ACF-style bonus.  For 10 points each:",
                    part1_text="Part 1.",
                    part1_answer="_answer 1_",
                    part2_text="Part 2.",
                    part2_answer="_answer 2_",
                    part3_text="Part 3",
                    part3_answer="_answer 3_",
                    author=writer,
                    question_type=acf_style_bonus)
bonus.save_question(QUESTION_CREATE, writer)

bonus = Bonus(
                    question_set=qset,
                    part1_text="~Part 1~ for VHSL bonus.",
                    part1_answer="_vhsl answer 1_",
                    author=writer,
                    question_type=vhsl_bonus)
bonus.save_question(QUESTION_CREATE, writer)

print "Done"
