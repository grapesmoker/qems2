# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0014_auto_20150117_1910'),
    ]

    operations = [
        migrations.AddField(
            model_name='bonus',
            name='category_entry',
            field=models.ForeignKey(to='qsub.CategoryEntry', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='category_entry',
            field=models.ForeignKey(to='qsub.CategoryEntry', null=True),
            preserve_default=True,
        ),
    ]
