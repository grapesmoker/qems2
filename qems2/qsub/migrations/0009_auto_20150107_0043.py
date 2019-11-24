# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0008_auto_20150107_0031'),
    ]

    operations = [
# This file had local changes I needed to get migrate to cooperate.
# You probably don't need this. -mbentley
#        migrations.CreateModel(
#            name='BonusHistory',
#            fields=[
#                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
#                ('leadin', models.CharField(max_length=500, null=True)),
#                ('part1_text', models.TextField()),
#                ('part1_answer', models.TextField()),
#                ('part2_text', models.TextField(null=True)),
#                ('part2_answer', models.TextField(null=True)),
#                ('part3_text', models.TextField(null=True)),
#                ('part3_answer', models.TextField(null=True)),
#                ('change_date', models.DateTimeField()),
#                ('changer', models.ForeignKey(to='qsub.Writer')),
#            ],
#            options={
#            },
#            bases=(models.Model,),
#        ),
#        migrations.CreateModel(
#            name='QuestionHistory',
#            fields=[
#                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
#            ],
#            options={
#            },
#            bases=(models.Model,),
#        ),
#        migrations.CreateModel(
#            name='TossupHistory',
#            fields=[
#                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
#                ('tossup_text', models.TextField()),
#                ('tossup_answer', models.TextField()),
#                ('change_date', models.DateTimeField()),
#                ('changer', models.ForeignKey(to='qsub.Writer')),
#                ('question_history', models.ForeignKey(to='qsub.QuestionHistory')),
#                ('question_type', models.ForeignKey(to='qsub.QuestionType', null=True)),
#            ],
#            options={
#            },
#            bases=(models.Model,),
#        ),
#        migrations.AddField(
#            model_name='bonushistory',
#            name='question_history',
#            field=models.ForeignKey(to='qsub.QuestionHistory'),
#            preserve_default=True,
#        ),
#        migrations.AddField(
#            model_name='bonushistory',
#            name='question_type',
#            field=models.ForeignKey(to='qsub.QuestionType', null=True),
#            preserve_default=True,
#        ),
#        migrations.AddField(
#            model_name='bonus',
#            name='created_date',
#            field=models.DateTimeField(default=datetime.datetime(2015, 1, 7, 6, 43, 26, 759092, tzinfo=utc)),
#            preserve_default=False,
#        ),
#        migrations.AddField(
#            model_name='bonus',
#            name='edited_date',
#            field=models.DateTimeField(null=True),
#            preserve_default=True,
#        ),
#        migrations.AddField(
#            model_name='bonus',
#            name='editor',
#            field=models.ForeignKey(related_name='bonus_editor', to='qsub.Writer', null=True),
#            preserve_default=True,
#        ),
#        migrations.AddField(
#            model_name='bonus',
#            name='last_changed_date',
#            field=models.DateTimeField(default=datetime.datetime(2015, 1, 7, 6, 43, 29, 833818, tzinfo=utc)),
#            preserve_default=False,
#        ),
#        migrations.AddField(
#            model_name='bonus',
#            name='question_history',
#            field=models.ForeignKey(to='qsub.QuestionHistory', null=True),
#            preserve_default=True,
#        ),
#        migrations.AddField(
#            model_name='tossup',
#            name='created_date',
#            field=models.DateTimeField(default=datetime.datetime(2015, 1, 7, 6, 43, 40, 396008, tzinfo=utc)),
#            preserve_default=False,
#        ),
#        migrations.AddField(
#            model_name='tossup',
#            name='edited_date',
#            field=models.DateTimeField(null=True),
#            preserve_default=True,
#        ),
#        migrations.AddField(
#            model_name='tossup',
#            name='editor',
#            field=models.ForeignKey(related_name='tossup_editor', to='qsub.Writer', null=True),
#            preserve_default=True,
#        ),
#        migrations.AddField(
#            model_name='tossup',
#            name='last_changed_date',
#            field=models.DateTimeField(default=datetime.datetime(2015, 1, 7, 6, 43, 43, 619858, tzinfo=utc)),
#            preserve_default=False,
#        ),
#        migrations.AddField(
#            model_name='tossup',
#            name='question_history',
#            field=models.ForeignKey(to='qsub.QuestionHistory', null=True),
#            preserve_default=True,
#        ),
        migrations.AddField(
            model_name='writer',
            name='send_mail_on_comments',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),    
    ]
