__author__ = 'mbentley'

import re
import json
import random
import string

from qems2.qsub.models import *
from qems2.qsub.model_utils import *

# TODO: Add tests
def create_acf_packet(qset, packet_name, created_by, regular_distribution, tiebreaker_distribution):
    packet = Packet.objects.create(question_set=qset, packet_name=packet_name, created_by=created_by, packet_type="ACF")
    packet.save()
    create_period_recursive(question_set, "ACF Regular Period", regular_distribution, packet)
    create_period_recursive(question_set, "ACF Tiebreaker Period", tiebreaker_distribution, packet)
    
# TODO: Add tests
def create_vhsl_packet(qset, tossup_distribution, bonus_distribution, tiebreaker_distribution):
    packet = Packet.objects.create(question_set=qset, packet_name=packet_name, created_by=created_by, packet_type="ACF")
    packet.save()
    create_period_recursive(question_set, "VHSL Tossup Period", tossup_distribution, packet)
    create_period_recursive(question_set, "VHSL Bonus Period", bonus_distribution, packet)
    create_period_recursive(question_set, "VHSL Tiebreaker Period", tiebreaker_distribution, packet)
    
# Creates a new period, figures out if it needs to create a new period entry, populates
# PeriodWideCategoryEntries and OnePeriodCategoryEntries appropriately
# TODO: Add tests
def create_period_recursive(question_set, period_type, distribution, packet):
    pwe, created = PeriodWideEntry.objects.get_or_create(question_set=qset, period_type=period_type, distribution=distribution)
    pwe.period_count += 1
    pwe.save()
    
    if (created):
        create_period_wide_category_entries(pwe)
        
    period = Period.objects.create(name=period_type, packet=packet, period_wide_entry=pwe)        
    create_one_period_category_entries(pwe, period)    

# TODO: Add tests
def create_period_wide_category_entries(period_wide_entry):
    categories = CategoryEntry.objects.filter(distribution=period_wide_entry.distribution)
    for category in categories:
        pwce = PeriodWideCategoryEntry.objects.create(period_wide_entry=period_wide_entry, category_entry=category)
        pwce.save()

# TODO: Add tests
def create_one_period_category_entries(period_wide_entry, period):
    period_wide_category_entries = PeriodWideCategoryEntry.objects.filter(period_wide_entry=period_wide_entry)
    for pwce in period_wide_category_entry:
        opce = OnePeriodCategoryEntry.objects.create(period=period, period_wide_category_entry=pwce)
        opce.save()

# TODO: Finish implementing
# TODO: Add tests
def set_packet_requirements(qset):
    clear_questions(qset)
    reset_category_counts(qsets, True)
    
    # Need to figure out total questions
    # When does probability come into play?
    
    packets = Packet.objects.filter(question_set=qset)
    for packet in packets:
        periods = Period.objects.filter(packet=packet)
        for period in periods:
            pass
                
    period_wide_entries = PeriodWideEntry.objects.filter(question_set=qset)
    for pwe in period_wide_entries:
        pass
    
# Determines if you've written enough questions to start packetization
# TODO: Add tests
def is_question_set_complete(qset):
    # Get every period-wide entry, see if requirement is satisfied
    all_periods_dict, per_period_dict = get_per_category_requirements_for_set(qset)
    for cat in all_periods_dict:
        req = all_periods_dict[cat]
        
        # Actually this isn't going to work, because we haven't assigned at the period category level
        
        
        if (not req.is_requirement_satisfied()):
            return False
    
    return True

# Returns a dictionary of requirements for all
# items in the set (spanning across periods).
# TODO: Add tests
def get_per_category_requirements_for_set(qset):    
    all_periods_dict = {} # Category Name to DistributionRequirement mapping
    period_wide_entries = PeriodWideEntry.objects.filter(question_set=qset)
    for pwe in period_wide_entries:
        period_wide_category_entries = PeriodWideCategoryEntry.objects.filter(period_wide_entry=pwe)
        for pwce in period_wide_category_entries:
            if (not str(pwce.category_entry) in all_periods_dict):
                # Calculate how many we've already written in this category from the set                
                # At the category level, I want to sum up anything that just matches my category name
                c = pwce.category_entry
                req = DistributionRequirement(c)
                if (c.sub_category_name is None or c.sub_category_name == ''):
                    # Return anything that matches category (implies sub and subsub match)
                    req.acf_tossups_written += len(Tossup.objects.filter(question_set=qset, category__category_name=c.category_name))
                    req.acf_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type="ACF-style bonus", category__category_name=c.category_name))
                    req.vhsl_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type="VHSL bonus",  category__category_name=c.category_name))
                elif (c.sub_sub_category_name is None or c.sub_sub_category_name == ''):
                    # Return anything that matches category and sub (implies subsub match)
                    req.acf_tossups_written += len(Tossup.objects.filter(question_set=qset, category__category_name=c.category_name, category__sub_category_name=c.sub_category_name))                    
                    req.acf_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type="ACF-style bonus", category__category_name=c.category_name, category__sub_category_name=c.sub_category_name))                    
                    req.vhsl_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type="VHSL bonus",  category__category_name=c.category_name, category__sub_category_name=c.sub_category_name))                    
                else:
                    # Just match on exact category--won't match subcategory because of the if statement
                    req.acf_tossups_written += len(Tossup.objects.filter(question_set=qset, category=c))
                    req.acf_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type="ACF-style bonus", category=c))
                    req.vhsl_bonuses_written += len(Bonus.objects.filter(question_set=qset, question_type="VHSL bonus",  category=c))
                
                all_periods_dict[str(pwce.category_entry)] = req
                
            req = all_periods_dict[str(pwce.category_entry)]
            
            req.acf_tossups_needed += pwce.acf_tossup_total_across_periods
            req.acf_bonuses_needed += pwce.acf_bonus_total_across_periods
            req.vhsl_bonuses_needed += pwce.vhsl_bonus_total_across_periods
            all_periods_dict[str(req)] = req # TODO: May not be needed
            
    return all_periods_dict

    
# Goes through the set and creates placeholder questions to enable to you to do packetization
# You will repalce these questions later
# TODO: Add tests
def fill_unassigned_questions(qset, author):
    # Get every period-wide entry, see if requirement is satisfied
    all_periods_dict = get_per_category_requirements_for_set(qset)
    for cat in all_periods_dict:
        req = all_periods_dict[cat]
        if (not req.is_requirement_satisfied()):
            # Now we need to add the appropriate number of questions
            # but we only really want to do this at the lowest level -- i.e. don't add
            # a question of category History and then another one of History - American            
            children = get_children_from_category_entry(cat)
            
            # If there's just 1 child, it means that we satisfy this set's needs by adding at this level
            if (len(children) == 1):
                difference = req.acf_tossups_needed - req.acf_tossups_written
                for i in range(0, difference):
                    tossup = Tossup.objects.create(question_set=qset, tossup_text="Placeholder Question for " + str(cat),
                        tossup_answer = "_Placeholder Answer_", author=author, question_type = "ACF-style tossup", 
                        location = "", time_period = "")
                    tossup.save()
                    
                difference = req.acf_bonuses_needed - req.acf_bonuses_written
                for i in range(0, difference):
                    bonus = Bonus.objects.create(question_set=qset, leadin="Placeholder Question for " + str(cat),
                        part1_text = "Placeholder question", part1_answer = "_Placeholder Answer_",
                        part2_text = "Placeholder question", part2_answer = "_Placeholder Answer_", 
                        part3_text = "Placeholder question", part3_answer = "_Placeholder Answer_",                 
                        author=author, question_type = "ACF-style bonus", location = "", time_period = "")
                    bonus.save()

                difference = req.acf_tossups_needed - req.acf_tossups_written
                for i in range(0, difference):
                    bonus = Bonus.objects.create(question_set=qset, leadin="",
                        part1_text = "Placeholder Question for " + str(cat), part1_answer = "_Placeholder Answer_",
                        part2_text = "", part2_answer = "",
                        part3_text = "", part3_answer = "",                   
                        author=author, question_type = "ACF-style bonus", location = "", time_period = "")
                    bonus.save()

# TODO: Add tests
def packetize(qset):
    if (not is_question_set_complete(qset)):
        print "Not enough questions in the set"
        return
    
    clear_questions(qset)
    reset_category_counts(qsets)
    
    packets = Packet.objects.filter(question_set=qset)
    for packet in packets:
        periods = Period.objects.filter(packet=packet)
        for period in periods:            
            distribution = Distribution.objects.get(distribution=period.period_wide_entry.distribution)
            
            assign_acf_tossups_to_period(qset, period, distribution)
            assign_acf_bonuses_to_period(qset, period, distribution)
            assign_vhsl_bonuses_to_period(qset, period, distribution)
            
            randomize_acf_tossups_in_period(qset, period)
            randomize_acf_bonuses_in_period(qset, period)
            randomize_vhsl_bonuses_in_period(qset, period)            
            
# TODO: Add tests
def randomize_acf_tossups_in_period(qset, period):
    tossups = get_assigned_acf_tossups_in_period(qset, period)
    
    # This is a naive algorithm that looks for best entropy between categories
    bestQuestionOrder = []
    bestDistance = 0
    for s in range(0, 50):
        curDistance = 0
        shuffle(tossups)
        last_seen = {}
        index = 0
        for tossup in tossups:
            top_level_cat = tossup.category.category_name
            if (top_level_cat in last_seen):
                curDistance += (index - last_seen[top_level_cat])
            last_seen[top_level_cat] = index            
            index += 1
        if (curDistance > bestDistance):
            bestQuestionOrder = tossups
            print "Best question distance: " + str(bestDistance)
            print "Set best question order: " + str(tossups)
    
    # Now that we have an order, set it
    index = 1
    for tossup in bestQuestionOrder:
        tossup.question_number = index
        tossup.save()
        index += 1    

# TODO: Add tests
def randomize_acf_bonuses_in_period(qset, period):
    bonuses = get_assigned_acf_bonuses_in_period(qset, period)
    randomize_bonuses_in_period(bonuses)
    
# TODO: Add tests
def randomize_vhsl_bonuses_in_period(qset, period):
    bonuses = get_assigned_vhsl_bonuses_in_period(qset, period)
    randomize_bonuses_in_period(bonuses)
   
# TODO: Reduce code duplication
# TODO: Add tests
def randomize_bonuses_in_period(bonuses):    
    # This is a naive algorithm that looks for best entropy between categories
    bestQuestionOrder = []
    bestDistance = 0
    for s in range(0, 50):
        curDistance = 0
        shuffle(bonuses)
        last_seen = {}
        index = 0
        for bonus in bonuses:
            top_level_cat = bonus.category.category_name
            if (top_level_cat in last_seen):
                curDistance += (index - last_seen[top_level_cat])
            last_seen[top_level_cat] = index            
            index += 1
        if (curDistance > bestDistance):
            bestQuestionOrder = bonuses
            print "Best question distance: " + str(bestDistance)
            print "Set best question order: " + str(bonuses)
    
    # Now that we have an order, set it
    index = 1
    for bonus in bestQuestionOrder:
        bonus.question_number = index
        bonus.save()
        index += 1   

# TODO: Add tests
def assign_acf_tossups_to_period(qset, period, distribution):
    acf_tossups = get_unassigned_acf_tossups(qset)    
    while (period.acf_tossup_cur < distribution.acf_tossup_per_packet_count):
        index = randint(0, len(acf_tossups) - 1)
        acf_tossup = acf_tossups[index]
        acf_tossups.remove(acf_tossup)
        if (is_acf_tossup_valid_in_period(qset, period, acf_tossup)):
            acf_tossup.packet = packet
            acf_tossup.period = period
            acf_tossup.save()
            period.acf_tossup_cur += 1
            period.save()
            
            # Update period-wide and one-period for this category
            c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(tossup.category, period)
            if (c_pwce is not None):
                c_pwce.acf_tossup_cur_across_periods += 1
                c_pwce.save()
            if (c_opce is not None):
                c_opce.acf_tossup_cur_in_period += 1
                c_opce.save()
            if (sc_pwce is not None):
                sc_pwce.acf_tossup_cur_across_periods += 1
                sc_pwce.save()
            if (sc_opce is not None):
                sc_opce.acf_tossup_cur_in_period += 1
                sc_opce.save()
            if (ssc_pwce is not None):
                ssc_pwce.acf_tossup_cur_across_periods += 1
                ssc_pwce.save()
            if (ssc_opce is not None):
                ssc_opce.acf_tossup_cur_in_period += 1
                ssc_opce.save()

# TODO: Figure out how to reduce code duplication
# TODO: Add tests
def assign_acf_bonuses_to_period(qset, period, distribution):
    acf_bonuses = get_unassigned_acf_bonuses(qset)
    
    while (period.acf_bonus_cur < distribution.acf_bonus_per_packet_count):
        index = randint(0, len(acf_bonuses) - 1)
        acf_bonus = acf_bonuses[index]
        acf_bonuses.remove(acf_bonus)
        if (is_acf_bonus_valid_in_period(qset, period, acf_bonus)):
            acf_bonus.packet = packet
            acf_bonus.period = period
            acf_bonus.save()
            period.acf_bonus_cur += 1
            period.save()
            
            # Update period-wide and one-period for this category
            c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(tossup.category, period)
            if (c_pwce is not None):
                c_pwce.acf_bonus_cur_across_periods += 1
                c_pwce.save()
            if (c_opce is not None):
                c_opce.acf_bonus_cur_in_period += 1
                c_opce.save()
            if (sc_pwce is not None):
                sc_pwce.acf_bonus_cur_across_periods += 1
                sc_pwce.save()
            if (sc_opce is not None):
                sc_opce.acf_bonus_cur_in_period += 1
                sc_opce.save()
            if (ssc_pwce is not None):
                ssc_pwce.acf_bonus_cur_across_periods += 1
                ssc_pwce.save()
            if (ssc_opce is not None):
                ssc_opce.acf_bonus_cur_in_period += 1
                ssc_opce.save() 
                        
# TODO: Figure out how to reduce code duplication
# TODO: Add tests
def assign_vhsl_bonuses_to_period(qset, period, distribution):
    vhsl_bonuses = get_unassigned_vhsl_bonuses(qset)    
    
    while (period.vhsl_bonus_cur < distribution.vhsl_bonus_per_packet_count):
        index = randint(0, len(vhsl_bonuses) - 1)
        vhsl_bonus = vhsl_bonuses[index]
        vhsl_bonuses.remove(vhsl_bonus)
        if (is_vhsl_bonus_valid_in_period(qset, period, vhsl_bonus)):
            vhsl_bonus.packet = packet
            vhsl_bonus.period = period
            vhsl_bonus.save()
            period.vhsl_bonus_cur += 1
            period.save()
            
            # Update period-wide and one-period for this category
            c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(tossup.category, period)
            if (c_pwce is not None):
                c_pwce.vhsl_bonus_cur_across_periods += 1
                c_pwce.save()
            if (c_opce is not None):
                c_opce.vhsl_bonus_cur_in_period += 1
                c_opce.save()
            if (sc_pwce is not None):
                sc_pwce.vhsl_bonus_cur_across_periods += 1
                sc_pwce.save()
            if (sc_opce is not None):
                sc_opce.vhsl_bonus_cur_in_period += 1
                sc_opce.save()
            if (ssc_pwce is not None):
                ssc_pwce.vhsl_bonus_cur_across_periods += 1
                ssc_pwce.save()
            if (ssc_opce is not None):
                ssc_opce.vhsl_bonus_cur_in_period += 1
                ssc_opce.save()  

# A category entry might be a sub-sub or sub category meaning that it has
# 1 or 2 parent categories.  This method returns the whole set
def get_parents_from_category_entry(category_entry):
    if (category_entry.sub_category_name is None or category_entry.sub_category_name == ''):
        return category_entry, None, None

    category_query = CategoryEntry.objects.filter(distribution=category_entry.distribution, category_name=category_entry.category_name, sub_category_name=None)
    category = None if (not category_query.exists()) else category_query[0]
    if (category_entry.sub_sub_category_name is None or category_entry.sub_sub_category_name == ''):
        return category, category_entry, None
    else:
        sub_category_query = CategoryEntry.objects.filter(distribution=category_entry.distribution, category_name=category_entry.category_name, sub_category_name=category_entry.sub_category_name, sub_sub_category_name=None)
        sub_category = None if (not sub_category_query.exists()) else sub_category_query[0]
        return category, sub_category, category_entry

# Gets the current entry and any children of this category.  For instance,
# "History" could return "History" and "History - European" and
# "History - European - British"
def get_children_from_category_entry(category_entry):
    if (category_entry.sub_category_name is None or category_entry.sub_category_name == ''):
        return CategoryEntry.objects.filter(distribution=category_entry.distribution, category_name=category_entry.category_name)
    elif (category_entry.sub_sub_category_name is None or category_entry.sub_sub_category_name == ''):
        return CategoryEntry.objects.filter(distribution=category_entry.distribution, category_name=category_entry.category_name, sub_category_name=category_entry.sub_category_name)
    else:
        # subsub categories don't have children
        return [category_entry]

# TODO: Add tests
def get_period_entries_from_category_entry_with_parents(category_entry, period):
    c, sc, ssc = get_parents_from_category_entry(category_entry)
    c_pwce, c_opce = get_period_entries_from_category_entry(c, period)
    sc_pwce, sc_opce = get_period_entries_from_category_entry(sc, period)
    ssc_pwce, ssc_opce = get_period_entries_from_category_entry(ssc, period)
    return c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce
                
def get_period_entries_from_category_entry(category_entry, period):    
    pwce = PeriodWideCategoryEntry.objects.get(period_wide_entry=period.period_wide_entry, category_entry=category_entry)
    opce = OnePeriodCategoryEntry.objects.get(period=period, period_wide_category_entry=pwce)
    return pwce, opce

# Make sure that we're under the limit period-wide and for just this period for all category combinations
# TODO: Add tests
def is_acf_tossup_valid_in_period(qset, period, tossup):
    c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(tossup.category, period)
    
    if (c_pwce is not None and c_pwce.acf_tossup_cur_across_periods >= c_pwce.acf_tossup_total_across_periods):
        return False
            
    if (c_opce is not None and c_opce.acf_tossup_cur_in_period >= c_opce.acf_tossup_total_in_period):
        return False

    if (c_opce is not None and c_opce.is_over_min_total_questions_limit()):
        return False
    
    if (sc_pwce is not None and sc_pwce.acf_tossup_cur_across_periods >= sc_pwce.acf_tossup_total_across_periods):
        return False
        
    if (sc_opce is not None and sc_opce.acf_tossup_cur_in_period >= sc_opce.acf_tossup_total_in_period):
        return False

    if (sc_opce is not None and sc_opce.is_over_min_total_questions_limit()):
        return False

    if (ssc_pwce is not None and ssc_pwce.acf_tossup_cur_across_periods >= ssc_pwce.acf_tossup_total_across_periods):
        return False
        
    if (ssc_opce is not None and ssc_opce.acf_tossup_cur_in_period >= ssc_opce.acf_tossup_total_in_period):
        return False

    if (ssc_opce is not None and ssc_opce.is_over_min_total_questions_limit()):
        return False
    
    return True

# TODO: Figure out how to reduce code duplication
# TODO: Add tests
def is_acf_bonus_valid_in_period(qset, period, bonus):
    c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(bonus.category, period)
    
    if (c_pwce is not None and c_pwce.acf_bonus_cur_across_periods >= c_pwce.acf_bonus_total_across_periods):
        return False
            
    if (c_opce is not None and c_opce.acf_bonus_cur_in_period >= c_opce.acf_bonus_total_in_period):
        return False

    if (c_opce is not None and c_opce.is_over_min_total_questions_limit()):
        return False
    
    if (sc_pwce is not None and sc_pwce.acf_bonus_cur_across_periods >= sc_pwce.acf_bonus_total_across_periods):
        return False
        
    if (sc_opce is not None and sc_opce.acf_bonus_cur_in_period >= sc_opce.acf_bonus_total_in_period):
        return False

    if (sc_opce is not None and sc_opce.is_over_min_total_questions_limit()):
        return False

    if (ssc_pwce is not None and ssc_pwce.acf_bonus_cur_across_periods >= ssc_pwce.acf_bonus_total_across_periods):
        return False
        
    if (ssc_opce is not None and ssc_opce.acf_bonus_cur_in_period >= ssc_opce.acf_bonus_total_in_period):
        return False

    if (ssc_opce is not None and ssc_opce.is_over_min_total_questions_limit()):
        return False
    
    return True
    
# TODO: Figure out how to reduce code duplication
# TODO: Add tests
def is_vhsl_bonus_valid_in_period(qset, period, bonus):
    c_pwce, c_opce, sc_pwce, sc_opce, ssc_pwce, ssc_opce = get_period_entries_from_category_entry_with_parents(bonus.category, period)
    
    if (c_pwce is not None and c_pwce.vhsl_bonus_cur_across_periods >= c_pwce.vhsl_bonus_total_across_periods):
        return False
            
    if (c_opce is not None and c_opce.vhsl_bonus_cur_in_period >= c_opce.vhsl_bonus_total_in_period):
        return False

    if (c_opce is not None and c_opce.is_over_min_total_questions_limit()):
        return False
    
    if (sc_pwce is not None and sc_pwce.vhsl_bonus_cur_across_periods >= sc_pwce.vhsl_bonus_total_across_periods):
        return False
        
    if (sc_opce is not None and sc_opce.vhsl_bonus_cur_in_period >= sc_opce.vhsl_bonus_total_in_period):
        return False

    if (sc_opce is not None and sc_opce.is_over_min_total_questions_limit()):
        return False

    if (ssc_pwce is not None and ssc_pwce.vhsl_bonus_cur_across_periods >= ssc_pwce.vhsl_bonus_total_across_periods):
        return False
        
    if (ssc_opce is not None and ssc_opce.vhsl_bonus_cur_in_period >= ssc_opce.vhsl_bonus_total_in_period):
        return False

    if (ssc_opce is not None and ssc_opce.is_over_min_total_questions_limit()):
        return False
    
    return True
    
def get_question_count_for_category_in_period(qset, period, category):
    if (type(category) is CategoryEntry):
        # TODO: Finish implementing
        pass
    elif (type(category) is SubCategoryEntry):
        pass
    elif (type(category) is SubSubCategoryEntry):
        pass
    else:
        pass
        # TODO: Throw some sort of exception

def get_unassigned_acf_tossups(qset):
    acf_tossups = Tossup.objects.filter(question_set=qset, packet=None)
    return acf_tossups
    
def get_unassigned_acf_bonuses(qset):
    question_type = get_question_type_from_string("ACF-style bonus")
    acf_bonuses = Bonus.objects.filter(question_set=qset, question_type=question_type, packet=None)
    return acf_bonuses
    
def get_unassigned_vhsl_bonuses(qset):
    question_type = get_question_type_from_string("VHSL bonus")
    vhsl_bonuses = Bonus.objects.filter(question_set=qset, question_type=question_type, packet=None)
    return vhsl_bonuses
    
def get_assigned_acf_tossups_in_period(qset, period):
    acf_tossups = Tossup.objects.filter(question_set=qset, period=period)
    return acf_tossups
    
def get_assigned_acf_bonuses_in_period(qset, period):
    question_type = get_question_type_from_string("ACF-style bonus")
    acf_bonuses = Bonus.objects.filter(question_set=qset, question_type=question_type, period=period)
    return acf_bonuses

def get_assigned_vhsl_bonuses_in_period(qset, period):
    question_type = get_question_type_from_string("VHSL bonus")
    vhsl_bonuses = Bonus.objects.filter(question_set=qset, question_type=question_type, period=period)
    return vhsl_bonuses

# Clear packet information from each question
def clear_questions(qset):
    
    tossups = Tossup.objects.filter(question_set=qset)
    for tossup in tossups:
        tossup.packet = None
        tossup.period = None
        tossup.question_number = None
        tossup.save()
    
    bonuses = Bonus.objects.filter(question_set=qset)
    for bonus in bonuses:
        bonus.packet = None
        bonus.period = None
        bonus.question_number = None
        bonus.save()
        
def reset_category_counts(qset, reset_totals=False):
    period_wide_entries = PeriodWideEntry.objects.filter(question_set=qset)
    for pwe in period_wide_entries:
        pwe.reset_current_values()
        if (reset_totals):
            pwe.reset_total_values()
        pwe.save()
        
        periods = Period.objects.filter(period_wide_entry=pwe)
        for period in periods:
            period.reset_current_values()
            period.save()
        
        period_wide_category_entries = PeriodWideCategoryEntry.objects.filter(period_wide_entry=pwe)        
        for pwce in period_wide_category_entries:
            pwce.reset_current_values()
            if (reset_totals):
                pwce.reset_total_values()
            pwce.save()
            
            one_period_category_entries = OnePeriodCategoryEntry.objects.filter(period_wide_category_entry=pwce)
            for opce in one_period_category_entries:
                opce.reset_current_values()
                if (reset_totals):
                    opce.reset_total_values()
                opce.save()

class DistributionRequirement():
    acf_tossups_written = 0
    acf_tossups_needed = 0
    acf_bonuses_written = 0
    acf_bonuses_needed = 0
    vhsl_bonuses_written = 0
    vhsl_bonuses_needed = 0
    category_entry = None
    period_name = ''
    
    def __init__(self, category_entry):
        self.category_entry = category_entry
    
    def __str__(self):
        return str(self.category_entry)
    
    def is_requirement_satisfied(self):
        if (self.acf_tossups_written < self.acf_tossups_needed):
            return False
            
        if (self.acf_bonuses_written < self.acf_bonuses_needed):
            return False
            
        if (self.vhsl_bonuses_writen < self.vhsl_bonuses_needed):
            return False
            
        return True
