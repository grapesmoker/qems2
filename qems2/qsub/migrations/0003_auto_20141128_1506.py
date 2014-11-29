# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0002_auto_20141123_1136'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tossup',
            name='created_date',
        ),
        migrations.RemoveField(
            model_name='tossup',
            name='updated_date',
        ),
        migrations.AlterField(
            model_name='bonus',
            name='leadin',
            field=models.CharField(max_length=500, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='bonus',
            name='part2_answer',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='bonus',
            name='part2_text',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='bonus',
            name='part3_answer',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='bonus',
            name='part3_text',
            field=models.TextField(null=True),
            preserve_default=True,
        ),
    ]
