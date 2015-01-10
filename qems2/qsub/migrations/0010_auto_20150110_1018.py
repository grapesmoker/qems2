# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0009_auto_20150107_0043'),
    ]

    operations = [
        migrations.RenameField(
            model_name='categoryentry',
            old_name='vhsl_tossup_fraction',
            new_name='vhsl_bonus_fraction',
        ),
        migrations.RenameField(
            model_name='subcategoryentry',
            old_name='vhsl_tossup_fraction',
            new_name='vhsl_bonus_fraction',
        ),
        migrations.RenameField(
            model_name='subsubcategoryentry',
            old_name='vhsl_tossup_fraction',
            new_name='vhsl_bonus_fraction',
        ),
    ]
