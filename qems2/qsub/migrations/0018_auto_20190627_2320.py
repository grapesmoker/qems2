# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0017_search_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='bonus',
            name='proofread',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='proofread_date',
            field=models.DateTimeField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='proofreader',
            field=models.ForeignKey(related_name='bonus_proofreader', to='qsub.Writer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='proofread',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='proofread_date',
            field=models.DateTimeField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='proofreader',
            field=models.ForeignKey(related_name='tossup_proofreader', to='qsub.Writer', null=True),
            preserve_default=True,
        ),
    ]
