# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0016_auto_20150211_2225'),
    ]

    operations = [
        migrations.AddField(
            model_name='bonus',
            name='search_question_answers',
            field=models.TextField(default=''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='search_question_content',
            field=models.TextField(default=''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='search_question_answers',
            field=models.TextField(default=''),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='search_question_content',
            field=models.TextField(default=''),
            preserve_default=True,
        ),    
        migrations.RemoveField(
            model_name='tossup',
            name='search_tossup_text',
        ),
        migrations.RemoveField(
            model_name='tossup',
            name='search_tossup_answer',
        ),
        migrations.RemoveField(
            model_name='bonus',
            name='search_leadin',
        ),
        migrations.RemoveField(
            model_name='bonus',
            name='search_part1_text',
        ),
        migrations.RemoveField(
            model_name='bonus',
            name='search_part1_answer',
        ),
        migrations.RemoveField(
            model_name='bonus',
            name='search_part2_text',
        ),
        migrations.RemoveField(
            model_name='bonus',
            name='search_part2_answer',
        ),
        migrations.RemoveField(
            model_name='bonus',
            name='search_part3_text',
        ),
        migrations.RemoveField(
            model_name='bonus',
            name='search_part3_answer',
        ),        
    ]
