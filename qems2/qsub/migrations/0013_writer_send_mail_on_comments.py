# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0012_auto_20150112_0043'),
    ]

    operations = [
        migrations.AddField(
            model_name='writer',
            name='send_mail_on_comments',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
