__author__ = 'jerry'

import datetime
from haystack import indexes
from qems2.qsub.models import Tossup, Bonus


class TossupIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    question_content = indexes.CharField(model_attr='search_question_content')
    question_answers = indexes.NgramField(model_attr='search_question_answers')
    author = indexes.CharField(model_attr='author')
    question_set = indexes.CharField(model_attr='question_set')

    def get_model(self):
        return Tossup

    def index_queryset(self, using=None):
        # TODO: change this to return only recently edited questions
        return self.get_model().objects.all()


class BonusIndex(indexes.SearchIndex, indexes.Indexable):

    text = indexes.CharField(document=True, use_template=True)
    question_content = indexes.CharField(model_attr='search_question_content')
    question_answers = indexes.NgramField(model_attr='search_question_answers')
    author = indexes.CharField(model_attr='author')
    question_set = indexes.CharField(model_attr='question_set')

    def get_model(self):
        return Bonus

    def index_queryset(self, using=None):
        # TODO: change this to return only recently edited questions
        return self.get_model().objects.all()
