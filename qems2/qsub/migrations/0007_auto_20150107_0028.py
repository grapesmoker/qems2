# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0006_auto_20150103_1527'),
    ]

    operations = [
        migrations.AddField(
            model_name='distribution',
            name='acf_bonus_per_period_count',
            field=models.PositiveIntegerField(default=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='distribution',
            name='acf_tossup_per_period_count',
            field=models.PositiveIntegerField(default=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='distribution',
            name='vhsl_bonus_per_period_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=False,
        ),
    ]
