# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0005_auto_20150103_1102'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questionset',
            name='max_acf_bonus_length',
            field=models.PositiveIntegerField(default=400),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='questionset',
            name='max_acf_tossup_length',
            field=models.PositiveIntegerField(default=750),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='questionset',
            name='max_vhsl_bonus_length',
            field=models.PositiveIntegerField(default=100),
            preserve_default=True,
        ),
    ]
