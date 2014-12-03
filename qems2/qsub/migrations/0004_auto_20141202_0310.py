# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0003_auto_20141128_1506'),
    ]

    operations = [
        migrations.AddField(
            model_name='tossup',
            name='search_tossup_text',
            field=models.TextField(default=''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='search_tossup_answer',
            field=models.TextField(default=''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='search_leadin',
            field=models.CharField(max_length=500, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='search_part1_answer',
            field=models.TextField(default=''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='search_part1_text',
            field=models.TextField(default=''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='search_part2_answer',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='search_part2_text',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='search_part3_answer',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='search_part3_text',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
    ]
