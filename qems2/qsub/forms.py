from django.contrib.auth.forms import UserCreationForm, UserChangeForm, ReadOnlyPasswordHashField, PasswordChangeForm
from django.contrib.auth.models import User
from django.db import models
from models import *
from utils import *
from django import forms
from django.utils.translation import ugettext, ugettext_lazy as _

class WriterCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):

        super(WriterCreationForm, self).__init__(*args, **kwargs)

        self.fields['password2'].widget.attrs.update({'placeholder': 'Enter the same password as above, for verification.'})
        self.fields['username'].widget.attrs.update({'placeholder': 'Thirty characters or fewer. Letters, digits, and @.-+_ are allowed.'})

class WriterChangeForm(forms.Form):

    def __init__(self, *args, **kwargs):

        super(WriterChangeForm, self).__init__(*args, **kwargs)

        self.fields['username'] = forms.CharField(max_length=200)
        self.fields['first_name'] = forms.CharField(max_length=200)
        self.fields['last_name'] = forms.CharField(max_length=200)
        self.fields['email'] = forms.EmailField(max_length=200)
        self.fields['send_mail_on_comments'] = forms.BooleanField(required=False)

        self.fields['username'].widget.attrs.update({'readonly': 'readonly'})

class QuestionSetForm(forms.ModelForm):

    class Meta:
        model = QuestionSet
        exclude = ['owner', 'public', 'address', 'host']

    def __init__(self, read_only=False, *args, **kwargs):
        super(QuestionSetForm, self).__init__(*args, **kwargs)

        self.fields['date'].widget.attrs.update({'placeholder': 'mm/dd/yyyy'})

        for field in self.fields:
            if read_only:
                self.fields[field].widget.attrs['readonly'] = True

class AddUserForm(forms.ModelForm):

    add_user = forms.BooleanField(required=False)

class RoleAssignmentForm(forms.ModelForm):

    class Meta:
        model = Role
        exclude = ['writer', 'question_set']

    def __init__(self, categories=None, *args, **kwargs):
        super(RoleAssignmentForm, self).__init__(*args, **kwargs)
        self.fields['category'] = forms.MultipleChoiceField(widget=forms.SelectMultiple(attrs={'size': len(CATEGORIES)}), choices=CATEGORIES)
        if categories:
            self.initial['category'] = categories

    #editor = forms.IntegerField(widget=forms.HiddenInput, required=True)
    #tournament = forms.IntegerField(widget=forms.HiddenInput, required=True)
    #categories = forms.MultipleChoiceField(widget=forms.SelectMultiple, choices=CATEGORIES)
    #can_view_others = forms.BooleanField(required=False)
    #can_edit_others = forms.BooleanField(required=False)

class TossupForm(forms.ModelForm):

    tossup_text = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}))
    tossup_answer = forms.CharField(widget=forms.Textarea(attrs={'rows': 1}))
    search_tossup_text = forms.CharField(widget=forms.HiddenInput, required=False)
    search_tossup_answer = forms.CharField(widget=forms.HiddenInput, required=False)
    question_history = forms.ModelChoiceField([], widget=forms.HiddenInput, required=False)
    editor = forms.ModelChoiceField([], widget=forms.HiddenInput, required=False)
    edited_date = forms.DateTimeField(widget=forms.HiddenInput, required=False)
    last_changed_date = forms.DateTimeField(widget=forms.HiddenInput, required=False)
    created_date = forms.DateTimeField(widget=forms.HiddenInput, required=False)

    category = forms.ModelChoiceField([])

    class Meta:
        model = Tossup
        exclude = ['question_set', 'subtype', 'time_period', 'location', 'question_number']

    def __init__(self, *args, **kwargs):
        qset_id = kwargs.pop('qset_id', None)
        packet_id = kwargs.pop('packet_id', None)
        role = kwargs.pop('role', None)
        writer = kwargs.pop('writer', None)

        super(TossupForm, self).__init__(*args, **kwargs)

        self.fields['question_type'] = forms.ModelChoiceField(queryset=QuestionType.objects.all(), required=False)
        self.fields['question_type'].widget.attrs['style'] = 'display:none'

        #self.fields['locked'].required = False

        if qset_id:
            try:
                qset = QuestionSet.objects.get(id=qset_id)
                all_writers = qset.writer.all() | qset.editor.all()
                if writer:
                    user = User.objects.get(username=writer)
                    my_writer = all_writers.get(user=user)
                    self.fields['author'] = forms.ModelChoiceField(queryset=all_writers, initial=my_writer.pk, required=True, empty_label=None)
                else:
                    self.fields['author'] = forms.ModelChoiceField(queryset=all_writers, required=True, empty_label=None)

                dist = qset.distribution
                dist_entries = dist.distributionentry_set.all()
                # categories = [(d.id, '{0!s} - {1!s}'.format(d.category, d.subcategory)) for d in dist_entries]
                if packet_id is not None:
                    pack_label = None
                    packets = qset.packet_set.filter(id=packet_id)
                else:
                    pack_label = 'N/A'
                    packets = qset.packet_set.all()
                self.fields['category'] = forms.ModelChoiceField(queryset=dist_entries, empty_label=None)
                self.fields['packet'] = forms.ModelChoiceField(queryset=packets, required=False, empty_label=pack_label)
            except QuestionSet.DoesNotExist:
                print 'Non-existent question set!'
                self.fields['category'] = forms.ModelChoiceField([], empty_label=None)

        if role and role == 'writer':
            # if this tossup is being submitted by a writer we don't need to show them the edited/locked checkboxes
            self.fields['locked'].widget.attrs['readonly'] = 'readonly'
            self.fields['locked'].widget.attrs['style'] = 'display:none'
            self.fields['locked'].label = ''
            self.fields['edited'].widget.attrs['readonly'] = 'readonly'
            self.fields['edited'].widget.attrs['style'] = 'display:none'
            self.fields['edited'].label = ''

class BonusForm(forms.ModelForm):

    leadin = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 100, 'rows': 2}), required=False)
    part1_text = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 100, 'rows': 2}))
    part1_answer = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 100, 'rows': 1}))
    part2_text = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 100, 'rows': 2}), required=False)
    part2_answer = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 100, 'rows': 1}), required=False)
    part3_text = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 100, 'rows': 2}), required=False)
    part3_answer = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 100, 'rows': 1}), required=False)
    search_leadin = forms.CharField(widget=forms.HiddenInput, required=False)
    search_part1_text = forms.CharField(widget=forms.HiddenInput, required=False)
    search_part1_answer = forms.CharField(widget=forms.HiddenInput, required=False)
    search_part2_text = forms.CharField(widget=forms.HiddenInput, required=False)
    search_part2_answer = forms.CharField(widget=forms.HiddenInput, required=False)
    search_part3_text = forms.CharField(widget=forms.HiddenInput, required=False)
    search_part3_answer = forms.CharField(widget=forms.HiddenInput, required=False)
    question_history = forms.ModelChoiceField([], widget=forms.HiddenInput, required=False)
    editor = forms.ModelChoiceField([], widget=forms.HiddenInput, required=False)
    edited_date = forms.DateTimeField(widget=forms.HiddenInput, required=False)
    last_changed_date = forms.DateTimeField(widget=forms.HiddenInput, required=False)
    created_date = forms.DateTimeField(widget=forms.HiddenInput, required=False)    

    class Meta:
        model = Bonus
        exclude = ['question_set', 'subtype', 'time_period', 'location', 'question_number']

    def __init__(self, *args, **kwargs):
        qset_id = kwargs.pop('qset_id', None)
        packet_id = kwargs.pop('packet_id', None)
        role = kwargs.pop('role', None)
        writer = kwargs.pop('writer', None)
        question_type = kwargs.pop('question_type', None)

        super(BonusForm, self).__init__(*args, **kwargs)

        self.fields['question_type'] = forms.ModelChoiceField(queryset=QuestionType.objects.all(), required=False)
        self.fields['question_type'].widget.attrs['style'] = 'display:none'

        if qset_id:
            try:
                qset = QuestionSet.objects.get(id=qset_id)
                all_writers = qset.writer.all() | qset.editor.all()
                if writer:
                    user = User.objects.get(username=writer)
                    my_writer = all_writers.get(user=user)
                    self.fields['author'] = forms.ModelChoiceField(queryset=all_writers, initial=my_writer.pk, required=True, empty_label=None)
                else:
                    self.fields['author'] = forms.ModelChoiceField(queryset=all_writers, required=True, empty_label=None)

                dist = qset.distribution
                dist_entries = dist.distributionentry_set.all()
                # categories = [(d.id, '{0!s} - {1!s}'.format(d.category, d.subcategory)) for d in dist_entries]
                if packet_id is not None:
                    pack_label = None
                    packets = qset.packet_set.filter(id=packet_id)
                else:
                    pack_label = 'N/A'
                    packets = qset.packet_set.all()
                self.fields['category'] = forms.ModelChoiceField(queryset=dist_entries, empty_label=None)
                self.fields['packet'] = forms.ModelChoiceField(queryset=packets, required=False, empty_label=pack_label)

            except QuestionSet.DoesNotExist:
                print 'Non-existent question set!'
                self.fields['category'] = forms.ModelChoiceField([], empty_label=None)

        if question_type and question_type == VHSL_BONUS:
            self.fields['leadin'].widget.attrs['style'] = 'display:none'
            self.fields['part2_text'].widget.attrs['style'] = 'display:none'
            self.fields['part2_answer'].widget.attrs['style'] = 'display:none'
            self.fields['part3_text'].widget.attrs['style'] = 'display:none'
            self.fields['part3_answer'].widget.attrs['style'] = 'display:none'

        if role and role == 'writer':
            # if this bonus is being submitted by a writer we don't need to show them the edited/locked checkboxes
            self.fields['locked'].widget.attrs['readonly'] = 'readonly'
            self.fields['locked'].widget.attrs['style'] = 'display:none'
            self.fields['locked'].label = ''
            self.fields['edited'].widget.attrs['readonly'] = 'readonly'
            self.fields['edited'].widget.attrs['style'] = 'display:none'
            self.fields['edited'].label = ''

class DistributionForm(forms.ModelForm):

    name = forms.CharField(max_length=100)

    class Meta:
        model = Distribution

class TieBreakDistributionForm(forms.ModelForm):

    name = forms.CharField(max_length=100)

    class Meta:
        model = TieBreakDistribution

class DistributionEntryForm(forms.ModelForm):

    entry_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    category = forms.CharField(max_length=100, widget=forms.TextInput(attrs={}))
    subcategory = forms.CharField(max_length=100, widget=forms.TextInput(attrs={}), required=False)
    min_tossups = forms.FloatField(widget=forms.NumberInput(attrs={}), min_value=0)
    min_bonuses = forms.FloatField(widget=forms.NumberInput(attrs={}), min_value=0)
    max_tossups = forms.FloatField(widget=forms.NumberInput(attrs={}), min_value=0)
    max_bonuses = forms.FloatField(widget=forms.NumberInput(attrs={}), min_value=0)

    delete = forms.BooleanField(widget=forms.CheckboxInput, required=False)

    class Meta:
        model = DistributionEntry
        exclude = ['distribution']

class TieBreakDistributionEntryForm(forms.Form):

    entry_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    category = forms.CharField(max_length=100, widget=forms.TextInput(attrs={}), required=False)
    subcategory = forms.CharField(max_length=100, widget=forms.TextInput(attrs={}), required=False)
    num_tossups = forms.FloatField(widget=forms.NumberInput(attrs={}), min_value=0)
    num_bonuses = forms.FloatField(widget=forms.NumberInput(attrs={}), min_value=0)

    delete = forms.BooleanField(widget=forms.CheckboxInput, required=False)

    #class Meta:
    #    model = DistributionEntry
    #    exclude = ['distribution']

class SetWideDistributionEntryForm(forms.Form):

    entry_id = forms.IntegerField(widget=forms.TextInput(attrs={'style': 'display: none'}))
    #dist_entry = forms.IntegerField(widget=forms.TextInput(attrs={'style': 'display: none'}))

    num_tossups = forms.IntegerField(widget=forms.NumberInput(attrs={}), min_value=0)
    num_bonuses = forms.IntegerField(widget=forms.NumberInput(attrs={}), min_value=0)

    category = forms.CharField(max_length=100, widget=forms.TextInput(attrs={}), required=False)
    subcategory = forms.CharField(max_length=100, widget=forms.TextInput(attrs={}), required=False)

    #class Meta:
    #    model = SetWideDistributionEntry
    #    exclude = ['min_tossups', 'max_tossups', 'min_bonuses', 'max_bonuses', 'question_set']

class PacketForm(forms.Form):

    packet_name = forms.CharField(max_length=200)

class QuestionUploadForm(forms.Form):

    questions_file = forms.FileField()

class NewPacketsForm(forms.Form):

    packet_name = forms.CharField(max_length=200, required=False)

    name_base = forms.CharField(max_length=190, required=False)
    num_packets = forms.IntegerField(widget=forms.NumberInput(attrs={}), required=False, min_value=0)

class TypeQuestionsForm(forms.Form):

    questions = forms.CharField(label='', widget=forms.Textarea(attrs={'rows': 10}), required=False)

class MoveTossupForm(forms.Form):
    def __init__(self, *args, **kwargs):
        move_sets = kwargs.pop('move_sets', None)

        super(MoveTossupForm, self).__init__(*args, **kwargs)

        self.fields['move_sets'] = forms.ModelChoiceField(queryset=move_sets, required=True)

class MoveBonusForm(forms.Form):
    def __init__(self, *args, **kwargs):
        move_sets = kwargs.pop('move_sets', None)

        super(MoveBonusForm, self).__init__(*args, **kwargs)

        self.fields['move_sets'] = forms.ModelChoiceField(queryset=move_sets, required=True)
        
