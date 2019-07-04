from django import forms
from django.forms import ModelForm


import re
import pprint as pp

chromosomes = [('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),('7','7'),('8','8'),('9','9'),('10','10'), ('11','11'), ('12','12') ,('13','13'),('14','14'), ('15', '15'), ('16','16'), ('17','17'), ('18','18'), ('19', '19'),('20','20'), ('21','21'), ('22','22'), ('X','X'), ('Y', 'Y'),]
references = [('grch37', 'grch37'),('grch38', 'grch38')]

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


class UserForm(forms.Form):
    chromosome_choice = forms.ChoiceField(choices=chromosomes)

class ReferenceForm(forms.Form):
    reference_choice = forms.ChoiceField(choices=references)

# class PositionForm(forms.Form): 
#     positions = forms.IntegerField(widget=forms.Textarea)

class TypeForm(forms.Form):
    position = forms.ChoiceField(choices = [("Position", "Position"),("Range", "Range"), ("Fusion", "Fusion"), ], widget = forms.RadioSelect, label = "Primer for:") 




class PositionForm(forms.Form): 
    # position = forms.ChoiceField(choices = [("Position", "Position")], widget = forms.CheckboxSelectMultiple)
    chromosome_choice = forms.ChoiceField(choices=chromosomes)
    coordinate = forms.IntegerField(min_value = 0, widget=forms.TextInput)
    reference_choice = forms.ChoiceField(choices=references)

    # def clean_release_number(self):
    #   chromosome_choice = self.cleaned_data.get["chromosome_choice"]
    #   coordinate = int(self.cleaned_data["coordinate"])
    #   reference_choice = self.cleaned_data["reference_choice"]

      # return chromosome_choice, coordinate, reference_choice
          

class RangeForm(forms.Form): 
    # position = forms.ChoiceField(choices = [("Range", "Range")], widget = forms.CheckboxSelectMultiple)
    chromosome_choice = forms.ChoiceField(choices=chromosomes)
    coordinate = forms.IntegerField(min_value = 0, widget=forms.TextInput)
    coordinate2 = forms.IntegerField(min_value = 0, widget=forms.TextInput, label = "2nd coordinate")
    reference_choice = forms.ChoiceField(choices=references)

class FusionForm(forms.Form): 
    # position = forms.ChoiceField(choices = [("Fusion", "Fusion")], widget = forms.CheckboxSelectMultiple)
    chromosome_choice = forms.ChoiceField(choices=chromosomes)
    coordinate = forms.IntegerField(min_value = 0, widget=forms.TextInput)
    strand = forms.ChoiceField(choices = [("1" , "1"), ("-1", "-1")])
    chromosome_choice2 = forms.ChoiceField(choices=chromosomes)
    coordinate2 = forms.IntegerField(min_value = 0, widget=forms.TextInput, label = "2nd coordinate")
    strand2 = forms.ChoiceField(choices = [("1" , "1"), ("-1", "-1")])
    reference_choice = forms.ChoiceField(choices=references)


            

        
