# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('qsub', '0013_writer_send_mail_on_comments'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryEntryForDistribution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('acf_tossup_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('acf_bonus_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('vhsl_bonus_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('min_total_questions_in_period', models.PositiveIntegerField(null=True)),
                ('max_total_questions_in_period', models.PositiveIntegerField(null=True)),
                ('category_entry', models.ForeignKey(to='qsub.CategoryEntry')),
                ('distribution', models.ForeignKey(to='qsub.Distribution')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='categoryentry',
            name='acf_bonus_fraction',
        ),
        migrations.RemoveField(
            model_name='categoryentry',
            name='acf_tossup_fraction',
        ),
        migrations.RemoveField(
            model_name='categoryentry',
            name='distribution',
        ),
        migrations.RemoveField(
            model_name='categoryentry',
            name='max_total_questions_in_period',
        ),
        migrations.RemoveField(
            model_name='categoryentry',
            name='min_total_questions_in_period',
        ),
        migrations.RemoveField(
            model_name='categoryentry',
            name='vhsl_bonus_fraction',
        ),
        migrations.RemoveField(
            model_name='oneperiodcategoryentry',
            name='acf_bonus_total_in_period',
        ),
        migrations.RemoveField(
            model_name='oneperiodcategoryentry',
            name='acf_tossup_total_in_period',
        ),
        migrations.RemoveField(
            model_name='oneperiodcategoryentry',
            name='vhsl_bonus_total_in_period',
        ),
        migrations.RemoveField(
            model_name='periodwidecategoryentry',
            name='category_entry',
        ),
        migrations.AddField(
            model_name='periodwidecategoryentry',
            name='category_entry_for_distribution',
            field=models.ForeignKey(to='qsub.CategoryEntryForDistribution', null=True),
            preserve_default=True,
        ),
    ]
