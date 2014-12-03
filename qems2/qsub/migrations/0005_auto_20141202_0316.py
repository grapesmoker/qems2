# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0004_auto_20141202_0310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bonus',
            name='search_leadin',
            field=models.CharField(default='', max_length=500, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='bonus',
            name='search_part2_answer',
            field=models.TextField(default='', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='bonus',
            name='search_part2_text',
            field=models.TextField(default='', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='bonus',
            name='search_part3_answer',
            field=models.TextField(default='', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='bonus',
            name='search_part3_text',
            field=models.TextField(default='', null=True),
            preserve_default=True,
        ),
    ]
