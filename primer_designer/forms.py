import re
import pprint as pp

from django import forms
from django.contrib import messages
from django.forms import ModelForm


class RegionsForm(forms.Form):
    """Form for entering regions to design primers on"""

    regions = forms.CharField(widget=forms.Textarea(
        attrs={
            'placeholder': "eg: name x:123213 grch37",
  
        }
    ))

    def clean_regions(self):

        cleaned_data = self.cleaned_data

        for line in cleaned_data['regions'].split("\n"):
           
            line = line.rstrip("\r")
            fields = line.split(" ")

            if (len(fields) != 3):
                # each line should have 3 pieces of information
                raise forms.ValidationError(
                    "{} does not contain the required 3 fields".format(line))

            if fields[2].lower() not in ['grch37', 'grch38']:
                # Check on valid reference names
                raise forms.ValidationError("{} invalid reference name".format(
                    fields[2]))

            pos_fields = re.split("[:-]", fields[1])

            if len(pos_fields) < 2:
                raise forms.ValidationError("Region needs a : between\
                    chromosome and position ({})".format(fields[1]))

            chromosomes = [str(x) for x in range(1, 23)]
            chromosomes.extend(['X', 'Y', 'MT'])
            print(chromosomes)
            # Check on valid chromosome names
            if pos_fields[0].upper() not in chromosomes:
                raise forms.ValidationError(
                    "{} is not a valid chromosome name".format(pos_fields[0]))

            for pos in pos_fields[1:]:
                try:
                    int(pos)
                except ValueError:
                    raise forms.ValidationError(
                        "{} positions is not an integer".format(pos))
