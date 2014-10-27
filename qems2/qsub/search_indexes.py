__author__ = 'jerry'

import datetime
from haystack import indexes
from qems2.qsub.models import Tossup, Bonus


class TossupIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    tossup_text = indexes.CharField(model_attr='tossup_text')
    tossup_answer = indexes.CharField(model_attr='tossup_answer')
    author = indexes.CharField(model_attr='author')

    def get_model(self):
        return Tossup

    def index_queryset(self, using=None):
        # TODO: change this to return only recently edited questions
        return self.get_model().objects.all()


class BonusIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    leadin = indexes.CharField(model_attr='leadin')
    part1_text = indexes.CharField(model_attr='part1_text')
    part2_text = indexes.CharField(model_attr='part2_text')
    part3_text = indexes.CharField(model_attr='part3_text')
    part1_answer = indexes.CharField(model_attr='part1_answer')
    part2_answer = indexes.CharField(model_attr='part2_answer')
    part3_answer = indexes.CharField(model_attr='part3_answer')

    def get_model(self):
        return Bonus

    def index_queryset(self, using=None):
        # TODO: change this to return only recently edited questions
        return self.get_model().objects.all()
