# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0011_auto_20150111_1520'),
    ]

    operations = [
        migrations.AddField(
            model_name='bonus',
            name='period',
            field=models.ForeignKey(to='qsub.Period', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='period',
            field=models.ForeignKey(to='qsub.Period', null=True),
            preserve_default=True,
        ),
    ]
