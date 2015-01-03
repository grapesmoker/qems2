# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0003_bonushistory_tossuphistory'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionset',
            name='max_acf_bonus_length',
            field=models.PositiveIntegerField(default=600),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='questionset',
            name='max_acf_tossup_length',
            field=models.PositiveIntegerField(default=750),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='questionset',
            name='max_vhsl_bonus_length',
            field=models.PositiveIntegerField(default=200),
            preserve_default=False,
        ),
    ]
