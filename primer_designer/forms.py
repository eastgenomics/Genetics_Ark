import re

from django import forms


class RegionsForm(forms.Form):
    """Form for entering regions to design primers on"""

    regions = forms.CharField(widget=forms.Textarea(
        attrs={
            'placeholder': 'Enter target region(s)',
            'style': 'padding-left: 10px; padding-top:10px'
        }
    ))

    def clean_regions(self):
        """Function to validate input regions"""
        cleaned_data = self.cleaned_data

        for line in cleaned_data['regions'].split("\n"):
            if line.count(':') > 1:
                # fusion design given, expected to be in the format
                # chr:pos:side:strand chr:pos:side:strand build fusion
                line = line.rstrip('fusion').strip().lower()

                fusion_pattern = r'^[a-b0-9]+:[0-9]+:[ab]:[-]?1\s+[a-b0-9]+:[0-9]+:[ab]:[-]?1\s+grch3[78]$'
                match = re.search(fusion_pattern, line)

                if not match:
                    raise forms.ValidationError(
                        f'Fusion design {line} not in the correct format'
                    )
            else:
                # normal design checking
                line = line.rstrip("\r")
                fields = line.split(" ")

                # strip empty spaces in cases where multiple spaces used
                fields = [x for x in fields if x]

                if len(fields) != 2:
                    # each line should have 2 pieces of information
                    raise forms.ValidationError((
                        f"{line} not in correct format. "
                        "Please see the examples for correct formatting"
                    ))

                if fields[-1].lower() not in ['grch37', 'grch38']:
                    # Check on valid reference names
                    raise forms.ValidationError("{} invalid reference\
                        name".format(fields[2]))

                # split chr and postion, will either be chr:pos or chr:pos-pos
                pos_fields = re.split("[:]", fields[0])
                match = re.search(r'^[0-9]+[-]?[0-9]*$', pos_fields[1])

                if not match:
                    raise forms.ValidationError(
                        f"{line} chr/position in wrong format"
                    )

                chromosomes = [str(x) for x in range(1, 23)]
                chromosomes.extend(['X', 'Y', 'MT'])

                # Check on valid chromosome names
                if pos_fields[0].upper() not in chromosomes:
                    raise forms.ValidationError(
                        f"{pos_fields[0]} is not a valid chromosome name")
