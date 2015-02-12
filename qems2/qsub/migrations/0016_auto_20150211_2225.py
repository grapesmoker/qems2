# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0015_auto_20150208_1930'),
    ]

    operations = [
        migrations.AddField(
            model_name='questionset',
            name='char_count_ignores_pronunciation_guides',
            field=models.BooleanField(default=True),
            preserve_default=True,
        ),
    ]
