from django import forms


class SearchForm(forms.Form):
    CHOICES = [
        ('BAM', 'BAM'),
        ('CNV', 'CNV')
        ]

    sample_id = forms.CharField(
        required=True,
        label='Sample ID',
        widget= forms.TextInput(
            attrs={
                'placeholder': 'Enter Sample ID',
                'class': 'form-control',
                'style': 'width:475px'
            }
        )
    )
    sample_type = forms.ChoiceField(
        widget= forms.Select(
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
