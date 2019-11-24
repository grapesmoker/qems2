from django.apps import AppConfig

class QSubConfig(AppConfig):
    name = 'qems2.qsub'
    verbose_name = 'QEMS2'
    
    def ready(self):
        print "Set up ready method"
