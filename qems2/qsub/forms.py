from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import models
from models import *
from django import forms

class WriterCreationForm(UserCreationForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super(WriterCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})

        #print self.fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].widget.attrs.update({'class': 'form-control'})

class QuestionSetForm(forms.ModelForm):
    
    class Meta:
        model = QuestionSet
        exclude = ['owner', 'public', 'address', 'host']
    
    def __init__(self, read_only=False, *args, **kwargs):
        super(QuestionSetForm, self).__init__(*args, **kwargs)

        for field in self.fields:
            if read_only:
                self.fields[field].widget.attrs['readonly'] = True

            self.fields[field].widget.attrs['class'] = 'form-control'

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
    
    tossup_text = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text field span8', 'cols': 40, 'rows': 12}))
    tossup_answer = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text field span8', 'cols': 40, 'rows': 5}))
    category = forms.ModelChoiceField([])

    class Meta:
        model = Tossup
        exclude = ['author', 'locked', 'question_set', 'subtype', 'time_period', 'location']

    def __init__(self, *args, **kwargs):
        qset_id = kwargs.pop('qset_id', None)
        super(TossupForm, self).__init__(*args, **kwargs)

        if qset_id:
            try:
                qset = QuestionSet.objects.get(id=qset_id)
                dist = qset.distribution
                dist_entries = dist.distributionentry_set.all()
                # categories = [(d.id, '{0!s} - {1!s}'.format(d.category, d.subcategory)) for d in dist_entries]
                packets = qset.packet_set.all()
                self.fields['category'] = forms.ModelChoiceField(queryset=dist_entries, empty_label=None)
                self.fields['packet'] = forms.ModelChoiceField(queryset=packets, required=False)
            except QuestionSet.DoesNotExist:
                print 'Non-existent question set!'
                self.fields['category'] = forms.ModelChoiceField([], empty_label=None)
        
class BonusForm(forms.ModelForm):
    
    leadin = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 80, 'rows': 2}))
    part1_text = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 80, 'rows': 2}))
    part1_answer = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 80, 'rows': 2}))
    part2_text = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 80, 'rows': 2}))
    part2_answer = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 80, 'rows': 2}))
    part3_text = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 80, 'rows': 2}))
    part3_answer = forms.CharField(widget=forms.Textarea(attrs={'class': 'question_text', 'cols': 80, 'rows': 2}))
    
    class Meta:
        model = Bonus
        exclude = ['author', 'locked', 'question_set', 'subtype', 'time_period', 'location']

    def __init__(self, *args, **kwargs):
        qset_id = kwargs.pop('qset_id', None)
        super(BonusForm, self).__init__(*args, **kwargs)

        if qset_id:
            try:
                qset = QuestionSet.objects.get(id=qset_id)
                dist = qset.distribution
                dist_entries = dist.distributionentry_set.all()
                # categories = [(d.id, '{0!s} - {1!s}'.format(d.category, d.subcategory)) for d in dist_entries]
                packets = qset.packet_set.all()
                self.fields['category'] = forms.ModelChoiceField(queryset=dist_entries, empty_label=None)
                self.fields['packet'] = forms.ModelChoiceField(queryset=packets, required=False)

            except QuestionSet.DoesNotExist:
                print 'Non-existent question set!'
                self.fields['category'] = forms.ModelChoiceField([], empty_label=None)

class DistributionForm(forms.ModelForm):
    
    name = forms.CharField(max_length=100)
    
    class Meta:
        model = Distribution
    
class DistributionEntryForm(forms.ModelForm):
    
    entry_id = forms.IntegerField(widget=forms.HiddenInput, required=False)
    category = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'width': 100}))
    subcategory = forms.CharField(max_length=100, widget=forms.TextInput(attrs={}), required=False)
    num_tossups = forms.IntegerField(widget=forms.TextInput(attrs={'width': 20, 'class': 'spinner'}))
    num_bonuses = forms.IntegerField(widget=forms.TextInput(attrs={'width': 20, 'class': 'spinner'}))
    fin_tossups = forms.IntegerField(widget=forms.TextInput(attrs={'width': 20, 'class': 'spinner'}), required=False)
    fin_bonuses = forms.IntegerField(widget=forms.TextInput(attrs={'width': 20, 'class': 'spinner'}), required=False)
    
    delete = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    
    class Meta:
        model = DistributionEntry
        exclude = ['distribution']

class PacketForm(forms.Form):

    packet_name = forms.CharField(max_length=200)

class NewPacketsForm(forms.Form):

    packet_name = forms.CharField(max_length=200, required=False)

    name_base = forms.CharField(max_length=190, required=False)
    num_packets = forms.IntegerField(widget=forms.TextInput(attrs={'class': 'spinner'}), required=False)