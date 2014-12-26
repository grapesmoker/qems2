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
                ('question_number', models.PositiveIntegerField(null=True)),
                ('search_leadin', models.CharField(default='', max_length=500, null=True)),
                ('search_part1_text', models.TextField(default='')),
                ('search_part1_answer', models.TextField(default='')),
                ('search_part2_text', models.TextField(default='', null=True)),
                ('search_part2_answer', models.TextField(default='', null=True)),
                ('search_part3_text', models.TextField(default='', null=True)),
                ('search_part3_answer', models.TextField(default='', null=True)),
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
            name='QuestionSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('date', models.DateField()),
                ('host', models.CharField(max_length=200)),
                ('address', models.TextField(max_length=200)),
                ('num_packets', models.PositiveIntegerField()),
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
                ('question_number', models.PositiveIntegerField(null=True)),
                ('search_tossup_text', models.TextField(default='')),
                ('search_tossup_answer', models.TextField(default='')),
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
                ('question_set_editor', models.ManyToManyField(related_name='editor', to='qsub.QuestionSet')),
                ('question_set_writer', models.ManyToManyField(related_name='writer', to='qsub.QuestionSet')),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
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
            name='packet',
            field=models.ForeignKey(to='qsub.Packet', null=True),
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
            model_name='distributionperpacket',
            name='question_set',
            field=models.ManyToManyField(to='qsub.QuestionSet'),
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
            name='packet',
            field=models.ForeignKey(to='qsub.Packet', null=True),
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
