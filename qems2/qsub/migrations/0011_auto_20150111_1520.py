# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0010_auto_20150110_1018'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnePeriodCategoryEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('acf_tossup_cur_in_period', models.PositiveIntegerField(default=0)),
                ('acf_bonus_cur_in_period', models.PositiveIntegerField(default=0)),
                ('vhsl_bonus_cur_in_period', models.PositiveIntegerField(default=0)),
                ('acf_tossup_total_in_period', models.PositiveIntegerField(null=True)),
                ('acf_bonus_total_in_period', models.PositiveIntegerField(null=True)),
                ('vhsl_bonus_total_in_period', models.PositiveIntegerField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Period',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('acf_tossup_cur', models.PositiveIntegerField(default=0)),
                ('acf_bonus_cur', models.PositiveIntegerField(default=0)),
                ('vhsl_bonus_cur', models.PositiveIntegerField(default=0)),
                ('packet', models.ForeignKey(to='qsub.Packet')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PeriodWideCategoryEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('acf_tossup_cur_across_periods', models.PositiveIntegerField(default=0)),
                ('acf_bonus_cur_across_periods', models.PositiveIntegerField(default=0)),
                ('vhsl_bonus_cur_across_periods', models.PositiveIntegerField(default=0)),
                ('acf_tossup_total_across_periods', models.PositiveIntegerField(null=True)),
                ('acf_bonus_total_across_periods', models.PositiveIntegerField(null=True)),
                ('vhsl_bonus_total_across_periods', models.PositiveIntegerField(null=True)),
                ('category_entry', models.ForeignKey(to='qsub.CategoryEntry')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PeriodWideEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('period_type', models.CharField(max_length=200)),
                ('acf_tossup_cur', models.PositiveIntegerField(default=0)),
                ('acf_bonus_cur', models.PositiveIntegerField(default=0)),
                ('vhsl_bonus_cur', models.PositiveIntegerField(default=0)),
                ('acf_tossup_total', models.PositiveIntegerField(null=True)),
                ('acf_bonus_total', models.PositiveIntegerField(null=True)),
                ('vhsl_bonus_total', models.PositiveIntegerField(null=True)),
                ('distribution', models.ForeignKey(to='qsub.Distribution')),
                ('question_set', models.ForeignKey(to='qsub.QuestionSet')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='subcategoryentry',
            name='category',
        ),
        migrations.RemoveField(
            model_name='subcategoryentry',
            name='distribution',
        ),
        migrations.RemoveField(
            model_name='subsubcategoryentry',
            name='distribution',
        ),
        migrations.RemoveField(
            model_name='subsubcategoryentry',
            name='subcategory',
        ),
        migrations.DeleteModel(
            name='SubCategoryEntry',
        ),
        migrations.DeleteModel(
            name='SubSubCategoryEntry',
        ),
        migrations.AddField(
            model_name='periodwidecategoryentry',
            name='period_wide_entry',
            field=models.ForeignKey(to='qsub.PeriodWideEntry'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='period',
            name='period_wide_entry',
            field=models.ForeignKey(to='qsub.PeriodWideEntry'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='oneperiodcategoryentry',
            name='period',
            field=models.ForeignKey(to='qsub.Period'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='oneperiodcategoryentry',
            name='period_wide_category_entry',
            field=models.ForeignKey(to='qsub.PeriodWideCategoryEntry'),
            preserve_default=True,
        ),
        migrations.RemoveField(
            model_name='categoryentry',
            name='category',
        ),
        migrations.AddField(
            model_name='categoryentry',
            name='category_name',
            field=models.CharField(default='default', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='categoryentry',
            name='category_type',
            field=models.CharField(default='Category', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='categoryentry',
            name='sub_category_name',
            field=models.CharField(max_length=200, null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='categoryentry',
            name='sub_sub_category_name',
            field=models.CharField(max_length=200, null=True),
            preserve_default=True,
        ),
    ]
