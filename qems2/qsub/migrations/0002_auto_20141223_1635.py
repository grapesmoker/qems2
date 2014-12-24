# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='bonus',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime(2014, 12, 23, 0, 0, 0, 0, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bonus',
            name='edited_date',
            field=models.DateTimeField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='editor',
            field=models.ForeignKey(related_name='bonus_editor', to='qsub.Writer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='last_changed_date',
            field=models.DateTimeField(default=datetime.datetime(2014, 12, 23, 0, 0, 0, 0, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='bonus',
            name='question_history',
            field=models.ForeignKey(to='qsub.QuestionHistory', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime(2014, 12, 23, 0, 0, 0, 0, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tossup',
            name='edited_date',
            field=models.DateTimeField(null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='editor',
            field=models.ForeignKey(related_name='tossup_editor', to='qsub.Writer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='last_changed_date',
            field=models.DateTimeField(default=datetime.datetime(2014, 12, 23, 0, 0, 0, 0, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='tossup',
            name='question_history',
            field=models.ForeignKey(to='qsub.QuestionHistory', null=True),
            preserve_default=True,
        ),
    ]
