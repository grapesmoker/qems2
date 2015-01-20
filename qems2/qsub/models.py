from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save

from datetime import datetime
from django.utils import timezone
import json

from collections import OrderedDict
from utils import *

# Create your models here.

CATEGORIES = (('S-P', 'Science - physics'),
              ('S-C', 'Science - chemistry'),
              ('S-B', 'Science - biology'),
              ('S-O', 'Science - other'),
              ('L-AM', 'Literature - American'),
              ('L-EU', 'Literature - European'),
              ('L-BR', 'Literature - British'),
              ('L-W', 'Literature - World'),
              ('H-AM', 'History - American'),
              ('H-EU', 'History - European'),
              ('H-W', 'History - World'),
              ('R', 'Religion'),
              ('M', 'Myth'),
              ('P', 'Philosophy'),
              ('FA', 'Fine arts'),
              ('SS', 'Social science'),
              ('G', 'Geography'),
              ('O', 'Other'),
              ('PC', 'Pop culture'))

RELIGION_SUBTYPES = (('R-J', 'Religion - Judaism'),
                     ('R-C', 'Religion - Christianity'),
                     ('R-B', 'Religion - Buddhism'),
                     ('R-H', 'Religion - Hinduism'),
                     ('R-I', 'Religion - Islam'),
                     ('R-O', 'Religion - Other'),)

MYTH_SUBTYPES = (('M-GR', 'Myth - Greek'),
                 ('M-R', 'Myth - Roman'),
                 ('M-N', 'Myth - Norse'),
                 ('M-BR', 'Myth - British Isles'),
                 ('M-EE', 'Myth - Eastern Europe'),
                 ('M-IN', 'Myth - India'),
                 ('M-CH', 'Myth - China'),
                 ('M-JP', 'Myth - Japan'),
                 ('M-O', 'Myth - Other'),)

PHILOSOPHY_SUBTYPES = (('P-AN', 'Philosophy - Analytic'),
                       ('P-CO', 'Philosophy - Continental'),
                       ('P-EN', 'Philosophy - Enlightenment'),
                       ('P-CL', 'Philosophy - Classical'),
                       ('P-O', 'Philosophy - Other'),)

FINE_ARTS_SUBTYPES = (('FA-M', 'Fine arts - Music'),
                      ('FA-SC', 'Fine arts - Sculpture'),
                      ('FA-OP', 'Fine arts - Opera'),
                      ('FA-F', 'Fine arts - Film'),
                      ('FA-P', 'Fine arts - Painting'),
                      ('FA-AR', 'Fine arts - Architecture'),
                      ('FA-O', 'Fine arts - Other'),)

SOCIAL_SCIENCE_SUBTYPES = (('SS-SOC', 'Social science - Sociology'),
                           ('SS-EC', 'Social science - Economics'),
                           ('SS-PS', 'Social science - Psychology'),
                           ('SS-O', 'Social science - Other'),)

LIT_SUBTYPES = (('L-PL', 'Literature - play'),
                ('L-PO', 'Literature - poem'),
                ('L-NO', 'Literature - novel'),
                ('L-CR', 'Literature - criticism'),
                ('L-O', 'Literature - other'),)

SCIENCE_SUBTYPES = (('S-P-QM', 'Science - physics - quantum mechanics'),
                    ('S-P-SM', 'Science - physics - statistical mechanics'),
                    ('S-P-M', 'Science - physics - classical mechanics'),
                    ('S-P-R', 'Science - physics - relativity'),
                    ('S-P-MP', 'Science - physics - mathematical physics'),
                    ('S-P-EM', 'Science - physics - electrodynamics'),
                    ('S-P-SS', 'Science - physics - solid state'),
                    ('S-P-MSC', 'Science - physics - miscellaneous'),
                    ('S-C-O', 'Science - chemistry - organic'),
                    ('S-C-P', 'Science - chemistry - physical'),
                    ('S-C-B', 'Science - chemistry - biochem'),
                    ('S-C-MSC', 'Science - chemistry - miscellaneous'),
                    ('S-B-C', 'Science - biology - biochem'),
                    ('S-B-G', 'Science - biology - genetics'),
                    ('S-B-E', 'Science - biology - evolutionary bio'),
                    ('S-B-MSC', 'Science - biology - miscellaneous'),
                    ('S-O-A', 'Science - other - astronomy'),
                    ('S-O-A', 'Science - other - mathematics'),
                    ('S-O-A', 'Science - other - computer science'),
                    ('S-O-A', 'Science - other - engineering'),
                    ('S-O-A', 'Science - other - earth science'),)

ACF_DISTRO = OrderedDict([('S', (5, 5)),
                          ('L', (5, 5)),
                          ('H', (5, 5)),
                          ('R', (1, 1)),
                          ('M', (1, 1)),
                          ('P', (1, 1)),
                          ('FA', (3, 3)),
                          ('SS', (1, 1)),
                          ('G', (1, 1)),
                          ('PC', (1, 1))])

class Writer (models.Model):

    user = models.OneToOneField(User)

    question_set_writer = models.ManyToManyField('QuestionSet', related_name='writer')
    question_set_editor = models.ManyToManyField('QuestionSet', related_name='editor')

    administrator = models.BooleanField(default=False)

    send_mail_on_comments = models.BooleanField(default=False)

    def __str__(self):
        return '{0!s} {1!s} ({2!s})'.format(self.user.first_name, self.user.last_name, self.user.username)

class QuestionSet (models.Model):
    name = models.CharField(max_length=200)
    date = models.DateField()
    host = models.CharField(max_length=200)
    address = models.TextField(max_length=200)
    owner = models.ForeignKey('Writer', related_name='owner')
    #public = models.BooleanField()
    num_packets = models.PositiveIntegerField()
    distribution = models.ForeignKey('Distribution') # TODO: This needs to be deleted eventually
    #teams = models.ForeignKey('Team')
    #tiebreak_dist = models.ForeignKey('TieBreakDistribution')
    max_acf_tossup_length = models.PositiveIntegerField(default=750)
    max_acf_bonus_length = models.PositiveIntegerField(default=400)
    max_vhsl_bonus_length = models.PositiveIntegerField(default=100)

    class Admin: pass

    def __str__(self):
        return '{0!s}'.format(self.name)

class Role(models.Model):

    writer = models.ForeignKey(Writer)
    question_set = models.ForeignKey(QuestionSet)
    category = models.CharField(max_length=500)
    can_view_others = models.BooleanField(default=False)
    can_edit_others = models.BooleanField(default=False)

class Packet (models.Model):
    packet_name = models.CharField(max_length=200)
    date_submitted = models.DateField(auto_now_add=True)
    # authors = models.ManyToManyField(Player)
    question_set = models.ForeignKey(QuestionSet)
    #team = models.ForeignKey(Team)

    created_by = models.ForeignKey(Writer, related_name='packet_creator')

    def __str__(self):
        return '{0!s}'.format(self.packet_name)

class DistributionPerPacket(models.Model):

    #packet = models.ManyToManyField(Packet)

    question_set = models.ManyToManyField(QuestionSet)
    category = models.CharField(max_length=10, choices=CATEGORIES)
    subcategory = models.CharField(max_length=10)
    num_tossups = models.PositiveIntegerField()
    num_bonuses = models.PositiveIntegerField()
    
    def __str__(self):
        return str("Distribution total for " + str(self.question_set))     

class Distribution(models.Model):

    name = models.CharField(max_length=100)
    acf_tossup_per_period_count = models.PositiveIntegerField()
    acf_bonus_per_period_count = models.PositiveIntegerField()
    vhsl_bonus_per_period_count = models.PositiveIntegerField()

    def __str__(self):
        return '{0!s}'.format(self.name)

# This class represents a category (i.e. History - European - British)
# It contains no distribution or set specific information
class CategoryEntry(models.Model):
    category_name = models.CharField(max_length=200)
    sub_category_name = models.CharField(max_length=200, null=True)
    sub_sub_category_name = models.CharField(max_length=200, null=True)
    category_type = models.CharField(max_length=200) # i.e. "Category", "SubCategory" or "SubSubCategory"
    
    def __str__(self):
        if (self.sub_sub_category_name is not None):
            return '{0!s} - {1!s} - {2!s}'.format(self.category_name, self.sub_category_name, self.sub_sub_category_name)
        elif (self.sub_category_name is not None):
            return '{0!s} - {1!s}'.format(self.category_name, self.sub_category_name)
        else:
            return '{0!s}'.format(self.category_name)

# This class links a Category Entry to a specific distribution.
# It contains data on how many questions per period this category entry
# should have.
class CategoryEntryForDistribution (models.Model):
    distribution = models.ForeignKey(Distribution)
    category_entry = models.ForeignKey(CategoryEntry)
    
    # Min/max questions of this type for one period
    # i.e. 2.2, which means between 2 and 3 weighted towards 2
    acf_tossup_fraction = models.DecimalField(null=True, max_digits=5, decimal_places=1)
    acf_bonus_fraction = models.DecimalField(null=True, max_digits=5, decimal_places=1)
    vhsl_bonus_fraction = models.DecimalField(null=True, max_digits=5, decimal_places=1)

    # Min/max questions of all types in one period for this category      
    min_total_questions_in_period = models.PositiveIntegerField(null=True)
    max_total_questions_in_period = models.PositiveIntegerField(null=True)
        
    def get_acf_tossup_integer(self):
        return int(self.acf_tossup_fraction)
        
    def get_acf_tossup_remainder(self):
        return round(self.acf_tossup_fraction - self.get_acf_tossup_integer(), 3)
    
    # Returns the maximum number of acf tossups based on the fraction.  For instance,
    # if you have a fraction of 4, it's 4.  If it's 4.2, it's 5 (since some packets can
    # legally have 5 tossups).
    def get_acf_tossup_upper_bound(self):
        if (self.get_acf_tossup_remainder() > 0):
            return self.get_acf_tossup_integer() + 1
        else:
            return self.get_acf_tossup_integer()

    def get_acf_bonus_integer(self):
        return int(self.acf_bonus_fraction)
        
    def get_acf_bonus_remainder(self):
        return round(self.acf_bonus_fraction - self.get_acf_bonus_integer(), 3)

    def get_acf_bonus_upper_bound(self):
        if (self.get_acf_bonus_remainder() > 0):
            return self.get_acf_bonus_integer() + 1
        else:
            return self.get_acf_bonus_integer()

    def get_vhsl_bonus_integer(self):
        return int(self.vhsl_bonus_fraction)
        
    def get_vhsl_bonus_remainder(self):
        return round(self.vhsl_bonus_fraction - self.get_vhsl_bonus_integer(), 3)

    def get_vhsl_bonus_upper_bound(self):
        if (self.get_vhsl_bonus_remainder() > 0):
            return self.get_vhsl_bonus_integer() + 1
        else:
            return self.get_vhsl_bonus_integer()

    def __str__(self):
        return str(self.category_entry)

# This class corresponds to all periods of this type in the set.  For instance,
# you'd have 10 ACFTossupBonusPeriods corresponding to this one PeriodWideEntry,
# and 10 ACFTossupBonusTiebreakerPeriods corresponding to a different PeriodWideEntry
class PeriodWideEntry (models.Model):
    period_type = models.CharField(max_length=200) # i.e. "ACF Regular Period"
    question_set = models.ForeignKey(QuestionSet)
    distribution = models.ForeignKey(Distribution)

    # Current number of questions across all categories
    acf_tossup_cur = models.PositiveIntegerField(default=0) 
    acf_bonus_cur = models.PositiveIntegerField(default=0) 
    vhsl_bonus_cur = models.PositiveIntegerField(default=0)
    
    # Total needed number of questions across all categories
    acf_tossup_total = models.PositiveIntegerField(null=True) 
    acf_bonus_total = models.PositiveIntegerField(null=True) 
    vhsl_bonus_total = models.PositiveIntegerField(null=True)
    
    def reset_current_values(self):
        self.acf_tossup_cur = 0  
        self.acf_bonus_cur = 0
        self.vhsl_bonus_cur = 0
        self.save()
        
    def reset_total_values(self):
        self.acf_tossup_total = 0
        self.acf_bonus_total = 0
        self.vhsl_bonus_total = 0
        self.save()

    def __str__(self):
        return str(self.period_type) + ' for ' + str(self.question_set)

# A period is a part of a packet.  For instance, it might be the regular tossup/bonus
# part of an mACF set.  It could also be the VHSL bonus round or a tiebreaker period.
class Period (models.Model):
    name = models.CharField(max_length=200) # i.e. "VHSL Tossup Period 1"
    packet = models.ForeignKey(Packet)
    period_wide_entry = models.ForeignKey(PeriodWideEntry)
    
    acf_tossup_cur = models.PositiveIntegerField(default=0) 
    acf_bonus_cur = models.PositiveIntegerField(default=0) 
    vhsl_bonus_cur = models.PositiveIntegerField(default=0)
 
    def reset_current_values(self):
        self.acf_tossup_cur = 0  
        self.acf_bonus_cur = 0
        self.vhsl_bonus_cur = 0
        self.save()
        
    def __str__(self):
        return str(self.name) 

# This class tracks the requirements for a particular category across all periods of this type
# in the set.  For instance, this might track how many History questions have currently been written
# and are still needed for the tiebreaker rounds in an ACF tournament.
class PeriodWideCategoryEntry(models.Model):
    period_wide_entry = models.ForeignKey(PeriodWideEntry)
    category_entry_for_distribution = models.ForeignKey(CategoryEntryForDistribution, null=True)
        
    # Current number of tossups/bonuses across all periods (with this distribution) for this category
    acf_tossup_cur_across_periods = models.PositiveIntegerField(default=0) 
    acf_bonus_cur_across_periods = models.PositiveIntegerField(default=0) 
    vhsl_bonus_cur_across_periods = models.PositiveIntegerField(default=0)    
    
    # Total expected number of tossups/bonuses across all periods (with this distribution) for this category
    acf_tossup_total_across_periods = models.PositiveIntegerField(null=True) 
    acf_bonus_total_across_periods = models.PositiveIntegerField(null=True) 
    vhsl_bonus_total_across_periods = models.PositiveIntegerField(null=True)
            
    def reset_current_values(self):
        self.acf_tossup_cur_across_periods = 0
        self.acf_bonus_cur_across_periods = 0
        self.vhsl_bonus_cur_across_periods = 0
        self.save()
        
    def reset_total_values(self):
        self.acf_tossup_total_across_periods = 0
        self.acf_bonus_total_across_periods = 0
        self.vhsl_bonus_total_across_periods = 0
        self.save()
        
    def get_category_type(self):
        return self.category_entry_for_distribution.category_entry.category_type

    def __str__(self):
        return 'Period-Wide {0!s}'.format(str(self.category_entry_for_distribution))

# This class tracks the requirements for a particular category in one period.
# For instance, it could track how many literature questions are needed in
# the VHSL bonus round (i.e. second period) of Round 5 of a tournament.
class OnePeriodCategoryEntry(models.Model):
    period = models.ForeignKey(Period)
    period_wide_category_entry = models.ForeignKey(PeriodWideCategoryEntry)
    
    # Current number of tossups/bonuses in this period for this category
    acf_tossup_cur_in_period = models.PositiveIntegerField(default=0) 
    acf_bonus_cur_in_period = models.PositiveIntegerField(default=0) 
    vhsl_bonus_cur_in_period = models.PositiveIntegerField(default=0)

    def get_linked_category_entry_for_distribution(self):
        return self.period_wide_category_entry.category_entry_for_distribution
        
    def get_total_questions_all_types(self):
        return self.acf_tossup_cur_in_period + self.acf_bonus_cur_in_period + self.vhsl_bonus_cur_in_period
        
    def is_under_max_total_questions_limit(self):
        max_total_questions = self.get_linked_category_entry_for_distribution().max_total_questions_in_period
        return (self.get_total_questions_all_types() <= max_total_questions)
        
    def is_over_min_total_questions_limit(self):
        min_total_questions = self.get_linked_category_entry_for_distribution().min_total_questions_in_period
        return (self.get_total_questions_all_types() >= min_total_questions)
        
    # TODO: This method should probably be renamed "is_over_max_acf_tossup_limit"
    def is_over_min_acf_tossup_limit(self):
        return (self.acf_tossup_cur_in_period > self.get_linked_category_entry_for_distribution().get_acf_tossup_upper_bound())

    def is_over_min_acf_bonus_limit(self):
        return (self.acf_bonus_cur_in_period > self.get_linked_category_entry_for_distribution().get_acf_bonus_upper_bound())

    def is_over_min_vhsl_bonus_limit(self):
        return (self.vhsl_bonus_cur_in_period > self.get_linked_category_entry_for_distribution().get_vhsl_bonus_upper_bound())

    def reset_current_values(self):
        self.acf_tossup_cur_in_period = 0
        self.acf_bonus_cur_in_period = 0
        self.vhsl_bonus_cur_in_period = 0
        self.save()
    
    def __str__(self):
        return 'Period {0!s}'.format(str(self.get_linked_category_entry_for_distribution()))


class TieBreakDistribution(models.Model):

    name = models.CharField(max_length=100)

    def __str__(self):
        return '{0!s}'.format(self.name)

# TODO: This should be deleted eventually
class DistributionEntry(models.Model):

    distribution = models.ForeignKey(Distribution)
    category = models.TextField()
    subcategory = models.TextField()
    min_tossups = models.PositiveIntegerField(null=True)
    min_bonuses = models.PositiveIntegerField(null=True)
    max_tossups = models.PositiveIntegerField(null=True)
    max_bonuses = models.PositiveIntegerField(null=True)

    #fin_tossups = models.CharField(max_length=500, null=True)
    #fin_bonuses = models.CharField(max_length=500, null=True)

    def __str__(self):
        return '{0!s} - {1!s}'.format(self.category, self.subcategory)

# TODO: This should be deleted eventually
class TieBreakDistributionEntry(models.Model):

    question_set = models.ForeignKey(QuestionSet)
    dist_entry = models.ForeignKey(DistributionEntry)
    num_tossups = models.PositiveIntegerField(null=True)
    num_bonuses = models.PositiveIntegerField(null=True)

    def __str__(self):
        return '{0!s} - {1!s}'.format(self.dist_entry.category, self.dist_entry.subcategory)

# TODO: This should be deleted eventually
class SetWideDistributionEntry(models.Model):

    question_set = models.ForeignKey(QuestionSet)
    dist_entry = models.ForeignKey(DistributionEntry)
    num_tossups = models.PositiveIntegerField()
    num_bonuses = models.PositiveIntegerField()

    def __str__(self):
        return '{0!s} - {1!s}'.format(self.dist_entry.category, self.dist_entry.subcategory)

class QuestionType(models.Model):

    question_type = models.CharField(max_length=500)

    def __unicode__(self):
        return '{0!s}'.format(self.question_type)

# Tossups and tossup history will both reference this, it's how you link
class QuestionHistory(models.Model):
    pass

class Tossup (models.Model):
    packet = models.ForeignKey(Packet, null=True)
    question_set = models.ForeignKey(QuestionSet)
    tossup_text = models.TextField()
    tossup_answer = models.TextField()
    period = models.ForeignKey(Period, null=True)

    category = models.ForeignKey(DistributionEntry, null=True) # TODO: Delete this later
    subtype = models.CharField(max_length=500)
    
    category_entry = models.ForeignKey(CategoryEntry, null=True)
    
    time_period = models.CharField(max_length=500)
    location = models.CharField(max_length=500)
    question_type = models.ForeignKey(QuestionType, null=True)
    author = models.ForeignKey(Writer)

    locked = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)

    #order = models.PositiveIntegerField(null=True)
    question_number = models.PositiveIntegerField(null=True)

    search_tossup_text = models.TextField(default='')
    search_tossup_answer = models.TextField(default='')

    question_history = models.ForeignKey(QuestionHistory, null=True)

    created_date = models.DateTimeField()
    last_changed_date = models.DateTimeField()
    edited_date = models.DateTimeField(null=True)
    editor = models.ForeignKey(Writer, null=True, related_name='tossup_editor')

    # Calculates character count, ignoring special characters
    def character_count(self):
        return get_character_count(self.tossup_text)

    def save(self, *args, **kwargs):
        self.setup_search_fields()
        super(Tossup, self).save(*args, **kwargs)

    def __unicode__(self):
        return '{0!s}...'.format(strip_markup(self.tossup_answer)[0:40]) #.decode('utf-8')

    def to_json(self):

        if self.packet is None:
            packet_id = None
        else:
            packet_id = self.packet.id
        if self.category is None:
            category_id = None
            category_name = ''
        else:
            category_id = self.category.id
            category_name = str(DistributionEntry.objects.get(id=self.category.id))
        return {'id': self.id,
                'packet': packet_id,
                'tossup_text': self.tossup_text.strip(),
                'tossup_answer': self.tossup_answer.strip(),
                'category': category_id,
                'category_name': category_name.strip(),
                'author': self.author.id,
                'question_number': self.question_number}

    def to_latex(self):

        html_to_latex_dict = {'u': 'uline', 'b': 'bf', 'strong': 'bf', 'i': 'it'}

        tossup_text = html_to_latex(self.tossup_text, html_to_latex_dict)
        tossup_answer = html_to_latex(self.tossup_answer, html_to_latex_dict)

        return r'\tossup{{{0}}}{{{1}}}'.format(tossup_text, tossup_answer) + '\n'

    def to_html(self, include_category=False, include_character_count=False):

        output = ''
        output = output + "<p>" + get_formatted_question_html(self.tossup_text, False, True, False) + "<br />"
        output = output + "ANSWER: " + get_formatted_question_html(self.tossup_answer, True, True, False) + "</p>"
        if (include_category and self.category is not None):
            output = output + "<p><strong>Category:</strong> " + str(self.category) + "</p>"
        else:
            output = output

        if (include_character_count):
            char_count = self.character_count()
            css_class = ''
            if (self.get_question_set() is not None):
                if (self.character_count() > self.question_set.max_acf_tossup_length):
                    css_class = "class='over-char-limit'"
                output = output + "<p><strong " + css_class + ">Character Count:</strong> " + str(self.character_count()) + "/" + str(self.question_set.max_acf_tossup_length) + "</p>"
            else:
                output = output + "<p><strong>Character Count:</strong> " + str(char_count) + "</p>"

        return output

    def is_valid(self):

        if self.tossup_text == '':
            raise InvalidTossup('question', self.tossup_text, self.question_number)

        if self.tossup_answer == '':
            raise InvalidTossup('answer', self.tossup_answer, self.question_number)

        if (not are_special_characters_balanced(self.tossup_text)):
            raise InvalidTossup('question', self.tossup_text, self.question_number)

        if (not are_special_characters_balanced(self.tossup_answer)):
            raise InvalidTossup('answer', self.tossup_answer, self.question_number)

        if (not does_answerline_have_underlines(self.tossup_answer)):
            raise InvalidTossup('answer', self.tossup_answer, self.question_number)

        return True

    def setup_search_fields(self):
        self.search_tossup_text = strip_special_chars(self.tossup_text)
        self.search_tossup_answer = strip_special_chars(self.tossup_answer)

    def get_question_set(self):
        try:
            return self.question_set
        except:
            return None

    def get_question_history(self):
        tossups = []
        bonuses = []

        if (self.question_history is not None):
            tossups = TossupHistory.objects.filter(question_history=self.question_history)
            bonuses = BonusHistory.objects.filter(question_history=self.question_history)

        return tossups, bonuses

    def save_question(self, edit_type, changer):
        print "Changer: " + str(changer)

        if (self.question_history is None):
            qh = QuestionHistory()
            qh.save()
            self.question_history = qh
            self.created_date = timezone.now()

        self.last_changed_date = timezone.now()
        if (edit_type == QUESTION_EDIT):
            self.editor = changer
            self.edited_date = timezone.now()

        print "Question History: " + str(self.question_history)

        tossup_history = TossupHistory()
        tossup_history.tossup_text = self.tossup_text
        tossup_history.tossup_answer = self.tossup_answer
        tossup_history.question_type = self.question_type
        tossup_history.question_history = self.question_history
        tossup_history.changer = changer
        tossup_history.change_date = timezone.now()
        tossup_history.save()

        self.save()

    def get_tossup_type(self):
        return get_tossup_type_from_question_type(self.question_type)

class Bonus(models.Model):
    packet = models.ForeignKey(Packet, null=True)
    question_set = models.ForeignKey(QuestionSet)
    period = models.ForeignKey(Period, null=True)    

    # Leadins and part 2 and 3 aren't required in VHSL, so allow nulls
    # The is_valid method will make sure that ACF bonuses have these values
    leadin = models.CharField(max_length=500, null=True)
    part1_text = models.TextField()
    part1_answer = models.TextField()
    part2_text = models.TextField(null=True)
    part2_answer = models.TextField(null=True)
    part3_text = models.TextField(null=True)
    part3_answer = models.TextField(null=True)

    category = models.ForeignKey(DistributionEntry, null=True) # TODO: Delete this later
    subtype = models.CharField(max_length=500)
    time_period = models.CharField(max_length=500)
    location = models.CharField(max_length=500)
    question_type = models.ForeignKey(QuestionType, null=True)

    category_entry = models.ForeignKey(CategoryEntry, null=True)

    question_history = models.ForeignKey(QuestionHistory, null=True)

    author = models.ForeignKey(Writer)

    locked = models.BooleanField(default=False)
    edited = models.BooleanField(default=False)

    #order = models.PositiveIntegerField(null=True)
    question_number = models.PositiveIntegerField(null=True)

    search_leadin = models.CharField(max_length=500, null=True, default='')
    search_part1_text = models.TextField(default='')
    search_part1_answer = models.TextField(default='')
    search_part2_text = models.TextField(null=True, default='')
    search_part2_answer = models.TextField(null=True, default='')
    search_part3_text = models.TextField(null=True, default='')
    search_part3_answer = models.TextField(null=True, default='')

    created_date = models.DateTimeField()
    last_changed_date = models.DateTimeField()
    edited_date = models.DateTimeField(null=True)
    editor = models.ForeignKey(Writer, null=True, related_name='bonus_editor')

    # Calculates character count, ignoring special characters
    def character_count(self):
        leadin_count = get_character_count(self.leadin)
        part1_count = get_character_count(self.part1_text)
        part2_count = get_character_count(self.part2_text)
        part3_count = get_character_count(self.part3_text)
        return leadin_count + part1_count + part2_count + part3_count

    def save(self, *args, **kwargs):
        self.setup_search_fields()
        super(Bonus, self).save(*args, **kwargs)

    def __unicode__(self):
        if (self.get_bonus_type() == ACF_STYLE_BONUS):
            return '{0!s}...'.format(strip_markup(get_answer_no_formatting(self.leadin))[0:40])
        else:
            return '{0!s}...'.format(strip_markup(get_answer_no_formatting(self.part1_answer))[0:40])

    def to_json(self):

        if self.packet is None:
            packet_id = None
        else:
            packet_id = self.packet.id
        if self.category is None:
            category_id = None
            category_name = ''
        else:
            category_id = self.category.id
            category_name = str(DistributionEntry.objects.get(id=self.category.id))

        return {'id': self.id,
                'packet': packet_id,
                'leadin': self.leadin.strip(),
                'part1_text': self.part1_text,
                'part1_answer': self.part1_answer,
                'part2_text': self.part2_text,
                'part2_answer': self.part2_answer,
                'part3_text': self.part3_text,
                'part3_answer': self.part3_answer,
                'category': category_id,
                'category_name': category_name.strip(),
                'author': self.author.id,
                'question_number': self.question_number}

    def to_latex(self):

        html_to_latex_dict = {'u': 'uline', 'b': 'bf', 'strong': 'bf', 'i': 'it'}

        leadin = html_to_latex(self.leadin, html_to_latex_dict)
        leadin = r'\begin{{bonus}}{{{0}}}'.format(leadin) + '\n'

        parts = [self.part1_text, self.part2_text, self.part3_text]
        answers = [self.part1_answer, self.part2_answer, self.part3_answer]

        parts_latex = ''

        for part, answer in zip(parts, answers):
            answer = html_to_latex(answer, html_to_latex_dict)
            part = html_to_latex(part, html_to_latex_dict)
            parts_latex += r'\bonuspart{{{0}}}{{{1}}}{{{2}}}'.format(10, part, answer) + '\n'

        return leadin + parts_latex + r'\end{bonus}' + '\n'

    def leadin_to_html(self):
        output = ''
        if (self.get_bonus_type() == ACF_STYLE_BONUS):
            return get_formatted_question_html(self.leadin, False, True, False)
        elif (self.get_bonus_type() == VHSL_BONUS):
            return get_formatted_question_html(self.part1_text, False, True, False)
        return output

    def to_html(self, include_category=False, include_character_count=False):
        output = ''

        if (self.get_bonus_type() == ACF_STYLE_BONUS):
            output = output + "<p>" + get_formatted_question_html(self.leadin, False, True, False) + "<br />"
            output = output + "[10] " + get_formatted_question_html(self.part1_text, False, True, False) + "<br />"
            output = output + "ANSWER: " + get_formatted_question_html(self.part1_answer, True, True, False) + "<br />"
            output = output + "[10] " + get_formatted_question_html(self.part2_text, False, True, False) + "<br />"
            output = output + "ANSWER: " + get_formatted_question_html(self.part2_answer, True, True, False) + "<br />"
            output = output + "[10] " + get_formatted_question_html(self.part3_text, False, True, False) + "<br />"
            output = output + "ANSWER: " + get_formatted_question_html(self.part3_answer, True, True, False) + "</p>"

            if (include_category and self.category is not None):
                output = output + "<p><strong>Category:</strong> " + str(self.category) + "</p>"

            if (include_character_count):
                char_count = self.character_count()
                css_class = ''
                if (self.get_question_set() is not None):
                    if (self.character_count() > self.question_set.max_acf_bonus_length):
                        css_class = "class='over-char-limit'"
                    output = output + "<p><strong " + css_class + ">Character Count:</strong> " + str(char_count) + "/" + str(self.question_set.max_acf_bonus_length) + "</p>"
                else:
                    output = output + "<p><strong>Character Count:</strong> " + str(char_count) + "</p>"

        elif (self.get_bonus_type() == VHSL_BONUS):
            output = output + "<p>" + get_formatted_question_html(self.part1_text, False, True, False) + "<br />"
            output = output + "ANSWER: " + get_formatted_question_html(self.part1_answer, True, True, False) + "</p>"

            if (include_category and self.category is not None):
                output = output + "<p><strong>Category:</strong> " + str(self.category) + "</p>"

            if (include_character_count):
                char_count = self.character_count()
                css_class = ''
                if (self.get_question_set() is not None):
                    if (self.character_count() > self.question_set.max_vhsl_bonus_length):
                        css_class = "class='over-char-limit'"
                    output = output + "<p><strong " + css_class + ">Character Count:</strong> " + str(char_count)  + "/" + str(self.question_set.max_vhsl_bonus_length) + "</p>"
                else:
                    output = output + "<p><strong>Character Count:</strong> " + str(char_count) + "</p>"

        return output

    def is_valid(self):

        if (self.get_bonus_type() == ACF_STYLE_BONUS):
            print "valid acf"

            if self.leadin == '':
                raise InvalidBonus('leadin', self.leadin, self.question_number)

            if (not are_special_characters_balanced(self.leadin)):
                raise InvalidBonus('leadin', self.leadin, self.question_number)

            answers = [self.part1_answer, self.part2_answer, self.part3_answer]
            for answer in answers:
                if (not are_special_characters_balanced(answer)):
                    raise InvalidBonus('answers', answer, self.question_number)
                if (not does_answerline_have_underlines(answer)):
                    raise InvalidBonus('answers', answer, self.question_number)

            parts = [self.part1_text, self.part2_text, self.part3_text]
            for part in parts:
                if part == '':
                    raise InvalidBonus('parts', part, self.question_number)
                if (not are_special_characters_balanced(part)):
                    raise InvalidBonus('parts', part, self.question_number)

            return True

        elif (self.get_bonus_type() == VHSL_BONUS):
            print "valid vhsl"

            if (self.leadin is not None and self.leadin != ''):
                raise InvalidBonus('leadin', self.leadin + " (this field should be blank for VHSL bonuses.)", self.question_number)
            blank_parts = [self.part2_text, self.part2_answer, self.part3_text, self.part3_answer]
            for blank_part in blank_parts:
                if (blank_part is not None and blank_part != ''):
                    raise InvalidBonus('2nd or 3rd part of bonus (this field should be blank for VHSL bonuses.)', blank_part, self.question_number)

            answers = [self.part1_answer]
            for answer in answers:
                if (not are_special_characters_balanced(answer)):
                    raise InvalidBonus('answer', answer, self.question_number)
                if (not does_answerline_have_underlines(answer)):
                    raise InvalidBonus('answer', answer, self.question_number)

            parts = [self.part1_text]
            for part in parts:
                if part == '':
                    raise InvalidBonus('part', part, self.question_number)
                if (not are_special_characters_balanced(part)):
                    raise InvalidBonus('part', part, self.question_number)

            return True

        else:
            raise InvalidBonus('question_type', self.question_type, self.question_number)

    def setup_search_fields(self):
        self.search_leadin = strip_special_chars(self.leadin)
        self.search_part1_text = strip_special_chars(self.part1_text)
        self.search_part1_answer = strip_special_chars(self.part1_answer)
        self.search_part2_text = strip_special_chars(self.part2_text)
        self.search_part2_answer = strip_special_chars(self.part2_answer)
        self.search_part3_text = strip_special_chars(self.part3_text)
        self.search_part3_answer = strip_special_chars(self.part3_answer)

    def get_question_set(self):
        try:
            return self.question_set
        except:
            return None

    def get_bonus_type(self):
        return get_bonus_type_from_question_type(self.question_type)

    def get_question_history(self):
        tossups = []
        bonuses = []

        if (self.question_history is not None):
            tossups = TossupHistory.objects.filter(question_history=self.question_history)
            bonuses = BonusHistory.objects.filter(question_history=self.question_history)
            print "is not null"

        return tossups, bonuses

    def save_question(self, edit_type, changer):
        if (self.question_history is None):
            qh = QuestionHistory()
            qh.save()
            self.question_history = qh
            self.created_date = timezone.now()

        self.last_changed_date = timezone.now()
        if (edit_type == QUESTION_EDIT):
            self.editor = changer
            self.edited_date = timezone.now()

        if (self.get_bonus_type() == VHSL_BONUS):
            self.leadin = ''
            self.part2_text  = ''
            self.part2_answer = ''
            self.part3_text = ''
            self.part3_answer = ''

        bonus_history = BonusHistory()
        bonus_history.leadin = self.leadin
        bonus_history.part1_text = self.part1_text
        bonus_history.part1_answer = self.part1_answer
        bonus_history.part2_text = self.part2_text
        bonus_history.part2_answer = self.part2_answer
        bonus_history.part3_text = self.part3_text
        bonus_history.part3_answer = self.part3_answer
        bonus_history.question_type = self.question_type
        bonus_history.question_history = self.question_history
        bonus_history.changer = changer
        bonus_history.change_date = timezone.now()
        bonus_history.save()
        self.save()

        print "bonus_history question_history: " + str(bonus_history.question_history.id)
        print "self.question_history: " + str(self.question_history.id)

class TossupHistory(models.Model):
    tossup_text = models.TextField()
    tossup_answer = models.TextField()
    changer = models.ForeignKey(Writer)
    change_date = models.DateTimeField()
    question_history = models.ForeignKey(QuestionHistory)
    question_type = models.ForeignKey(QuestionType, null=True)

    def __unicode__(self):
        return '{0!s}...'.format(strip_markup(self.tossup_answer)[0:40]) #.decode('utf-8')

    def to_html(self):
        output = ''
        output = output + "<p>" + get_formatted_question_html(self.tossup_text, False, True, False) + "<br />"
        output = output + get_formatted_question_html(self.tossup_answer, True, True, False) + "<br />"
        output = output + "Changed by " + str(self.changer) + " on " + str(self.change_date) + "</p>"
        return output

class BonusHistory(models.Model):
    leadin = models.CharField(max_length=500, null=True)
    part1_text = models.TextField()
    part1_answer = models.TextField()
    part2_text = models.TextField(null=True)
    part2_answer = models.TextField(null=True)
    part3_text = models.TextField(null=True)
    part3_answer = models.TextField(null=True)
    changer = models.ForeignKey(Writer)
    change_date = models.DateTimeField()
    question_history = models.ForeignKey(QuestionHistory)
    question_type = models.ForeignKey(QuestionType, null=True)

    def to_html(self):
        output = ''
        if (self.get_bonus_type() == ACF_STYLE_BONUS):
            output = output + "<p>" + get_formatted_question_html(self.leadin, False, True, False) + "<br />"
            output = output + "[10] " + get_formatted_question_html(self.part1_text, False, True, False) + "<br />"
            output = output + "ANSWER: " + get_formatted_question_html(self.part1_answer, True, True, False) + "<br />"
            output = output + "[10] " + get_formatted_question_html(self.part2_text, False, True, False) + "<br />"
            output = output + "ANSWER: " + get_formatted_question_html(self.part2_answer, True, True, False) + "<br />"
            output = output + "[10] " + get_formatted_question_html(self.part3_text, False, True, False) + "<br />"
            output = output + "ANSWER: " + get_formatted_question_html(self.part3_answer, True, True, False) + "<br />"
        else:
            output = output + "<p>" + get_formatted_question_html(self.part1_text, False, True, False) + "<br />"
            output = output + "ANSWER: " + get_formatted_question_html(self.part1_answer, True, True, False) + "<br />"

        output = output + "Changed by <strong>" + str(self.changer) + "</strong> on <strong>" + str(self.change_date) + "</strong></p>"
        return output

    def __unicode__(self):
        if (self.get_bonus_type() == ACF_STYLE_BONUS):
            return '{0!s}...'.format(strip_markup(get_answer_no_formatting(self.leadin))[0:40])
        else:
            return '{0!s}...'.format(strip_markup(get_answer_no_formatting(self.part1_answer))[0:40])

    def get_bonus_type(self):
        return get_bonus_type_from_question_type(self.question_type)

class Tag(models.Model):

    pass

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Writer.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)

