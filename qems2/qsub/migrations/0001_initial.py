# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bonus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('leadin', models.CharField(max_length=500, null=True)),
                ('part1_text', models.TextField()),
                ('part1_answer', models.TextField()),
                ('part2_text', models.TextField(null=True)),
                ('part2_answer', models.TextField(null=True)),
                ('part3_text', models.TextField(null=True)),
                ('part3_answer', models.TextField(null=True)),
                ('subtype', models.CharField(max_length=500)),
                ('time_period', models.CharField(max_length=500)),
                ('location', models.CharField(max_length=500)),
                ('locked', models.BooleanField(default=False)),
                ('edited', models.BooleanField(default=False)),
                ('proofread', models.BooleanField(default=False)),
                ('question_number', models.PositiveIntegerField(null=True)),
                ('search_question_content', models.TextField(default='')),
                ('search_question_answers', models.TextField(default='')),
                ('created_date', models.DateTimeField()),
                ('last_changed_date', models.DateTimeField()),
                ('edited_date', models.DateTimeField(null=True)),
                ('proofread_date', models.DateTimeField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
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
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CategoryEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category_name', models.CharField(max_length=200)),
                ('sub_category_name', models.CharField(max_length=200, null=True)),
                ('sub_sub_category_name', models.CharField(max_length=200, null=True)),
                ('category_type', models.CharField(max_length=200)),
                ('acf_tossup_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('acf_bonus_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('vhsl_bonus_fraction', models.DecimalField(null=True, max_digits=5, decimal_places=1)),
                ('min_total_questions_in_period', models.PositiveIntegerField(null=True)),
                ('max_total_questions_in_period', models.PositiveIntegerField(null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Distribution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('acf_tossup_per_period_count', models.PositiveIntegerField(default=20)),
                ('acf_bonus_per_period_count', models.PositiveIntegerField(default=20)),
                ('vhsl_bonus_per_period_count', models.PositiveIntegerField(default=0)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DistributionEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.TextField()),
                ('subcategory', models.TextField()),
                ('min_tossups', models.PositiveIntegerField(null=True)),
                ('min_bonuses', models.PositiveIntegerField(null=True)),
                ('max_tossups', models.PositiveIntegerField(null=True)),
                ('max_bonuses', models.PositiveIntegerField(null=True)),
                ('distribution', models.ForeignKey(to='qsub.Distribution')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DistributionPerPacket',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(max_length=10, choices=[('S-P', 'Science - physics'), ('S-C', 'Science - chemistry'), ('S-B', 'Science - biology'), ('S-O', 'Science - other'), ('L-AM', 'Literature - American'), ('L-EU', 'Literature - European'), ('L-BR', 'Literature - British'), ('L-W', 'Literature - World'), ('H-AM', 'History - American'), ('H-EU', 'History - European'), ('H-W', 'History - World'), ('R', 'Religion'), ('M', 'Myth'), ('P', 'Philosophy'), ('FA', 'Fine arts'), ('SS', 'Social science'), ('G', 'Geography'), ('O', 'Other'), ('PC', 'Pop culture')])),
                ('subcategory', models.CharField(max_length=10)),
                ('num_tossups', models.PositiveIntegerField()),
                ('num_bonuses', models.PositiveIntegerField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
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
            name='Packet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('packet_name', models.CharField(max_length=200)),
                ('date_submitted', models.DateField(auto_now_add=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
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
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('date', models.DateField()),
                ('host', models.CharField(max_length=200)),
                ('address', models.TextField(max_length=200)),
                ('num_packets', models.PositiveIntegerField()),
                ('max_acf_tossup_length', models.PositiveIntegerField(default=750)),
                ('max_acf_bonus_length', models.PositiveIntegerField(default=400)),
                ('max_vhsl_bonus_length', models.PositiveIntegerField(default=100)),
                ('char_count_ignores_pronunciation_guides', models.BooleanField(default=True)),
                ('distribution', models.ForeignKey(to='qsub.Distribution')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='QuestionType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question_type', models.CharField(max_length=500)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(max_length=500)),
                ('can_view_others', models.BooleanField(default=False)),
                ('can_edit_others', models.BooleanField(default=False)),
                ('question_set', models.ForeignKey(to='qsub.QuestionSet')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SetWideDistributionEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_tossups', models.PositiveIntegerField()),
                ('num_bonuses', models.PositiveIntegerField()),
                ('dist_entry', models.ForeignKey(to='qsub.DistributionEntry')),
                ('question_set', models.ForeignKey(to='qsub.QuestionSet')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TieBreakDistribution',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TieBreakDistributionEntry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_tossups', models.PositiveIntegerField(null=True)),
                ('num_bonuses', models.PositiveIntegerField(null=True)),
                ('dist_entry', models.ForeignKey(to='qsub.DistributionEntry')),
                ('question_set', models.ForeignKey(to='qsub.QuestionSet')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tossup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tossup_text', models.TextField()),
                ('tossup_answer', models.TextField()),
                ('subtype', models.CharField(max_length=500)),
                ('time_period', models.CharField(max_length=500)),
                ('location', models.CharField(max_length=500)),
                ('locked', models.BooleanField(default=False)),
                ('edited', models.BooleanField(default=False)),
                ('proofread', models.BooleanField(default=False)),
                ('question_number', models.PositiveIntegerField(null=True)),
                ('search_question_content', models.TextField(default='')),
                ('search_question_answers', models.TextField(default='')),
                ('created_date', models.DateTimeField()),
                ('last_changed_date', models.DateTimeField()),
                ('edited_date', models.DateTimeField(null=True)),
                ('proofread_date', models.DateTimeField(null=True)),
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
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Writer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('administrator', models.BooleanField(default=False)),
                ('send_mail_on_comments', models.BooleanField(default=False)),
                ('question_set_editor', models.ManyToManyField(related_name='editor', to='qsub.QuestionSet')),
                ('question_set_writer', models.ManyToManyField(related_name='writer', to='qsub.QuestionSet')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
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
            model_name='tossuphistory',
            name='changer',
            field=models.ForeignKey(to='qsub.Writer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossuphistory',
            name='question_history',
            field=models.ForeignKey(to='qsub.QuestionHistory'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossuphistory',
            name='question_type',
            field=models.ForeignKey(to='qsub.QuestionType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='author',
            field=models.ForeignKey(to='qsub.Writer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='category',
            field=models.ForeignKey(to='qsub.DistributionEntry', null=True),
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
            name='packet',
            field=models.ForeignKey(to='qsub.Packet', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='period',
            field=models.ForeignKey(to='qsub.Period', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='proofreader',
            field=models.ForeignKey(related_name='tossup_proofreader', to='qsub.Writer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='question_history',
            field=models.ForeignKey(to='qsub.QuestionHistory', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='question_set',
            field=models.ForeignKey(to='qsub.QuestionSet'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='tossup',
            name='question_type',
            field=models.ForeignKey(to='qsub.QuestionType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='role',
            name='writer',
            field=models.ForeignKey(to='qsub.Writer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='questionset',
            name='owner',
            field=models.ForeignKey(related_name='owner', to='qsub.Writer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='periodwideentry',
            name='question_set',
            field=models.ForeignKey(to='qsub.QuestionSet'),
            preserve_default=True,
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
            model_name='percategorywritersettings',
            name='writer_question_set_settings',
            field=models.ForeignKey(to='qsub.WriterQuestionSetSettings'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='packet',
            name='created_by',
            field=models.ForeignKey(related_name='packet_creator', to='qsub.Writer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='packet',
            name='question_set',
            field=models.ForeignKey(to='qsub.QuestionSet'),
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
        migrations.AddField(
            model_name='distributionperpacket',
            name='question_set',
            field=models.ManyToManyField(to='qsub.QuestionSet'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='categoryentry',
            name='distribution',
            field=models.ForeignKey(to='qsub.Distribution'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonushistory',
            name='changer',
            field=models.ForeignKey(to='qsub.Writer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonushistory',
            name='question_history',
            field=models.ForeignKey(to='qsub.QuestionHistory'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonushistory',
            name='question_type',
            field=models.ForeignKey(to='qsub.QuestionType', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='author',
            field=models.ForeignKey(to='qsub.Writer'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='category',
            field=models.ForeignKey(to='qsub.DistributionEntry', null=True),
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
            name='packet',
            field=models.ForeignKey(to='qsub.Packet', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='period',
            field=models.ForeignKey(to='qsub.Period', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='proofreader',
            field=models.ForeignKey(related_name='bonus_proofreader', to='qsub.Writer', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='question_history',
            field=models.ForeignKey(to='qsub.QuestionHistory', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='question_set',
            field=models.ForeignKey(to='qsub.QuestionSet'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bonus',
            name='question_type',
            field=models.ForeignKey(to='qsub.QuestionType', null=True),
            preserve_default=True,
        ),
    ]
