from django import forms
from django.forms import ModelForm

class SearchForm(forms.Form):
    sampleID = forms.CharField(required = True, widget=forms.TextInput(attrs={
        'placeholder':'Enter Sample ID',
        'class': 'form-control',
        'style': 'width:150px'
        }))

class urlForm(forms.Form):
    bam_url_form = forms.CharField(required = True, widget=forms.TextInput(attrs={
        'placeholder':'Enter BAM url',
        'class': 'form-control',
        'style': 'width:500px'
        }))
    idx_url_form = forms.CharField(required = True, widget=forms.TextInput(attrs={
        'placeholder':'Enter Index url',
        'class': 'form-control',
        'style': 'width:500px'
        }))