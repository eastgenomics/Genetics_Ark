from django import forms
from django.forms import ModelForm

class SearchForm(forms.Form):
    sampleID = forms.CharField(required = True, widget=forms.TextInput(attrs={
        'placeholder':'Enter Sample ID',
        'class': 'form-control',
        'style': 'width:150px'
        }))