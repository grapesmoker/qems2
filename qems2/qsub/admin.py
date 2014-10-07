from django.contrib import admin
from models import *

admin.site.register(QuestionSet)
admin.site.register(Packet)
admin.site.register(Tossup)
admin.site.register(Bonus)
admin.site.register(Writer)
admin.site.register(Distribution)
admin.site.register(DistributionEntry)
admin.site.register(DistributionPerPacket)
admin.site.register(SetWideDistributionEntry)
admin.site.register(QuestionType)
admin.site.register(TieBreakDistributionEntry)
