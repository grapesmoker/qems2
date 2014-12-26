If you already have a working database and you're having problems applying the initial change, try the following:

1. Change 0001_initial.py to be like this:

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
    ]


2. Run "python manage.py migrate"
3. You'll probably get an error.
4. Revert the change to 0001_initial.py (i.e. put it back to what's in the repository)
5. Run "python manage.py migrate" again--it shoudl work this time

All changes to models.py in the future should be accompanied by doing this:
1. Run "python manage.py makemigrations qsub"
2. Run "python manage.py migrate"
