__author__ = 'jerry'

import datetime
from haystack import indexes
from qems2.qsub.models import Tossup, Bonus


class TossupIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    tossup_text = indexes.CharField(model_attr='search_tossup_text')
    tossup_answer = indexes.CharField(model_attr='search_tossup_answer')
    author = indexes.CharField(model_attr='author')
    question_set = indexes.CharField(model_attr='question_set')

    def get_model(self):
        return Tossup

    def index_queryset(self, using=None):
        # TODO: change this to return only recently edited questions
        return self.get_model().objects.all()


class BonusIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    leadin = indexes.CharField(model_attr='search_leadin')
    part1_text = indexes.CharField(model_attr='search_part1_text')
    part2_text = indexes.CharField(model_attr='search_part2_text')
    part3_text = indexes.CharField(model_attr='search_part3_text')
    part1_answer = indexes.CharField(model_attr='search_part1_answer')
    part2_answer = indexes.CharField(model_attr='search_part2_answer')
    part3_answer = indexes.CharField(model_attr='search_part3_answer')
    author = indexes.CharField(model_attr='author')
    question_set = indexes.CharField(model_attr='question_set')



    def get_model(self):
        return Bonus

    def index_queryset(self, using=None):
        # TODO: change this to return only recently edited questions
        return self.get_model().objects.all()
