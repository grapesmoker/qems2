# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0012_auto_20150112_0043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='distribution',
            name='acf_bonus_per_period_count',
            field=models.PositiveIntegerField(default=20),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='distribution',
            name='acf_tossup_per_period_count',
            field=models.PositiveIntegerField(default=20),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='distribution',
            name='vhsl_bonus_per_period_count',
            field=models.PositiveIntegerField(default=0),
            preserve_default=True,
        ),
    ]
