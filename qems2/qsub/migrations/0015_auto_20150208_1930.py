# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0013_auto_20150119_0324'),
    ]

    operations = [
        migrations.CreateModel(
            name='PerCategoryWriterSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email_on_new_questions', models.BooleanField(default=False)),
                ('email_on_new_comments', models.BooleanField(default=False)),
                ('distribution_entry', models.ForeignKey(to='qsub.DistributionEntry')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='WriterQuestionSetSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email_on_all_new_comments', models.BooleanField(default=False)),
                ('email_on_all_new_questions', models.BooleanField(default=False)),
                ('question_set', models.ForeignKey(to='qsub.QuestionSet')),
                ('writer', models.ForeignKey(to='qsub.Writer')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='percategorywritersettings',
            name='writer_question_set_settings',
            field=models.ForeignKey(to='qsub.WriterQuestionSetSettings'),
            preserve_default=True,
        ),
    ]
