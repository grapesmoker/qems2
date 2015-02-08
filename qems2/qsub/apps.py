from django.apps import AppConfig
from qems2.qsub.signals import *

class QSubConfig(AppConfig):
    name = 'qems2.qsub'
    verbose_name = 'QEMS2'
    
    def ready(self):
        print "Set up ready method"
