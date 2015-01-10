# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0007_auto_20150107_0028'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('acf_tossup_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('acf_bonus_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('vhsl_tossup_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('min_total_questions_in_period', models.PositiveIntegerField(null=True)),
                ('max_total_questions_in_period', models.PositiveIntegerField(null=True)),
                ('category', models.TextField()),
                ('distribution', models.ForeignKey(to='qsub.Distribution')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubCategoryEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('acf_tossup_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('acf_bonus_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('vhsl_tossup_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('min_total_questions_in_period', models.PositiveIntegerField(null=True)),
                ('max_total_questions_in_period', models.PositiveIntegerField(null=True)),
                ('subcategory', models.TextField()),
                ('category', models.ForeignKey(to='qsub.CategoryEntry')),
                ('distribution', models.ForeignKey(to='qsub.Distribution')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SubSubCategoryEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('acf_tossup_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('acf_bonus_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('vhsl_tossup_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('min_total_questions_in_period', models.PositiveIntegerField(null=True)),
                ('max_total_questions_in_period', models.PositiveIntegerField(null=True)),
                ('subsubcategory', models.TextField()),
                ('distribution', models.ForeignKey(to='qsub.Distribution')),
                ('subcategory', models.ForeignKey(to='qsub.SubCategoryEntry')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
