# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0002_auto_20141223_1635'),
    ]

    operations = [
        migrations.CreateModel(
            name='BonusHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('leadin', models.CharField(max_length=500, null=True)),
                ('part1_text', models.TextField()),
                ('part1_answer', models.TextField()),
                ('part2_text', models.TextField(null=True)),
                ('part2_answer', models.TextField(null=True)),
                ('part3_text', models.TextField(null=True)),
                ('part3_answer', models.TextField(null=True)),
                ('change_date', models.DateTimeField()),
                ('changer', models.ForeignKey(to='qsub.Writer')),
                ('question_history', models.ForeignKey(to='qsub.QuestionHistory')),
                ('question_type', models.ForeignKey(to='qsub.QuestionType', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TossupHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tossup_text', models.TextField()),
                ('tossup_answer', models.TextField()),
                ('change_date', models.DateTimeField()),
                ('changer', models.ForeignKey(to='qsub.Writer')),
                ('question_history', models.ForeignKey(to='qsub.QuestionHistory')),
                ('question_type', models.ForeignKey(to='qsub.QuestionType', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
