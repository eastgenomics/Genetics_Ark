from django import forms
from django.forms import ModelForm


import re
import pprint as pp

class RegionsForm( forms.Form ):
    """
    Form for adding a new company to the database. 

    """
    
    regions = forms.CharField(widget=forms.Textarea)

    def clean_regions( self ):

        cleaned_data = self.cleaned_data

        for line in cleaned_data['regions'].split("\n"):
            print "'{}'".format( line )
            line = line.rstrip("\r") 
            fields = re.split(r'[\t ]+', line)
                
            # each line should have 3 pieces of information
            if (len(fields) != 3):
                raise forms.ValidationError("{} does not contain the required 3 fields".format( line ) )

            # Check on valid reference names
            if fields[2].lower() not in ['grch37', 'grch38' ]:
                raise forms.ValidationError("{} invalid reference name".format( fields[2] ) )

            pos_fields = re.split("[:-]", fields[ 1 ])

            print ("Fields:", "--".join(pos_fields))

            if len( pos_fields ) < 2:
                raise forms.ValidationError("Region needs a : between chromosome and position ({})".format( fields[ 1] ) )
                
            # Check on valid chromosome names
            if pos_fields[0].upper() not in ['1','2','3','4','5','6','7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', 'X', 'Y', 'MT' ]:
                raise forms.ValidationError("{} is not a valid chromosome name".format( pos_fields[0] ) )

            for pos in pos_fields[1:]:
                try: 
                    int(pos)

                except ValueError:
                    raise forms.ValidationError("{} positions is not an integer".format( pos ) )



            

        
