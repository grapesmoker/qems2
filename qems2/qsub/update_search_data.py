from models import *

def update_search_data():
    tossups = Tossup.objects.all()
    for tossup in tossups:
        tossup.setup_search_fields()
        tossup.save()
    
    bonuses = Bonus.objects.all()
    for bonus in bonuses:
        bonus.setup_search_fields()
        bonus.save()
    
