# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tossup',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime(2014, 11, 23, 11, 36, 7, 391803), verbose_name='date created'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='tossup',
            name='updated_date',
            field=models.DateTimeField(default=datetime.datetime(2014, 11, 23, 11, 36, 7, 391830), verbose_name='date updated'),
            preserve_default=True,
        ),
    ]
