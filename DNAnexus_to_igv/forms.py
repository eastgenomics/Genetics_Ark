from django import forms
from django.core.exceptions import ValidationError


class SearchForm(forms.Form):
    CHOICES = [
        ('BAM', 'BAM'),
        ('CNV', 'CNV')
        ]

    sample_id = forms.CharField(
        required=True,
        label='Sample ID',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter Sample ID',
                'class': 'form-control',
                'style': 'width:475px'
            }
        )
    )
    sample_type = forms.ChoiceField(
        widget=forms.Select(
            attrs={
                'class': 'form-group',
                'style': 'width:475px'
            }
        ),
        label='Sample Type',
        choices=CHOICES,
        required=True
    )


class UrlForm(forms.Form):
    file_url = forms.CharField(
        required=True,
        label='BAM URL',
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Enter BAM URL',
                'class': 'form-control',
                'style': 'width:500px',
                'rows': 2,
                'name': 'file_url'
            }
        )
    )
    index_url = forms.CharField(
        required=True,
        label='Index URL',
        widget=forms.Textarea(
            attrs={
                'placeholder': 'Enter BAM Index URL',
                'class': 'form-control',
                'style': 'width:500px',
                'rows': 2,
                'name': 'index_url'
            }
        )
    )

    def clean(self):
        file_url = self.cleaned_data['file_url']
        index_url = self.cleaned_data['index_url']

        if "https://" not in file_url or 'https://' not in index_url:
            raise ValidationError("Please check your link!")
