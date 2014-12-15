# This script creates standard question types, creates a 
# typical ACF distribution and adds some questions

from qems2.qsub.models import *
from datetime import datetime

# Set this to an existing user in the database
# TODO: Probably just create a new user in the future
username = "admin2"

print "Starting script"

#distribution = Distribution.objects.get(name="Default Distribution")

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

question_type = QuestionType(question_type="ACF-style tossup")
question_type.save()

question_type = QuestionType(question_type="ACF-style bonus")
question_type.save()

question_type = QuestionType(question_type="VHSL bonus")
question_type.save()

user = User.objects.get(username=username)
writer = Writer.objects.get(user=user)

qset = QuestionSet(
                    name="Default Question Set",
                    date=datetime.today(),
                    host="Default Host",
                    address="Foo",
                    owner=writer,
                    distribution=distribution,
                    num_packets=10)
qset.save()                    

for dist_entry in DistributionEntry.objects.filter(distribution=distribution):
    swde = SetWideDistributionEntry(
                                    question_set=qset,
                                    dist_entry=dist_entry,
                                    num_tossups=(10*dist_entry.max_tossups),
                                    num_bonuses=(10*dist_entry.max_bonuses))
    swde.save()


tossup = Tossup(
                    question_set=qset,
                    tossup_text="Test ~tossup 1~.",
                    tossup_answer="test _answer 1_",
                    author=writer)
tossup.setup_search_fields()
tossup.save()
                    
tossup = Tossup(
                    question_set=qset,
                    tossup_text="Test ~tossup 2~.",
                    tossup_answer="test _answer 2_",
                    author=writer)
tossup.setup_search_fields()
tossup.save()                    

print "Done"
