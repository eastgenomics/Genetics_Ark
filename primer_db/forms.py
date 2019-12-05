from django import forms
from django.forms import ModelForm
from datetime import datetime
from .models import PrimerDetails, Coordinates, Status, Scientist, PCRProgram, Buffer 
from django.core.exceptions import ValidationError

class PrimerForm(forms.Form):
	name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter primer name'}))
	gene = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter gene name'}))
	comments = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder':'Other comments'}))
	buffer = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Buffer'}), initial="Buffer D")
	pcr_program = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'PCR Program'}), initial = "TD65_55")	
	forename = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Scientist Forename'}))
	surname = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Scientist Surname'}))


class SequenceForm(forms.Form):
	sequence = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter primer sequence', 'autocomplete': 'off'}))

	def clean(self):
		data = self.cleaned_data["sequence"]

		for nucl in data:
			nucl = nucl.upper()

			if nucl not in ["A", "T", "C", "G"]:
				raise forms.ValidationError("Nucleotide sequence cannot contains anything other than ATCG")

		return self.cleaned_data


class ArrivalDateForm(forms.Form):
	this_year = datetime.now().year
	arrival_date = forms.DateField(widget=forms.SelectDateWidget(years=range(this_year - 5,this_year + 3)), 
		initial=datetime.now)


class StatusLocationForm(forms.Form):
	CHOICES = (('On order', 'On order'), ('In Bank', 'In Bank'), ('Archived', 'Archived'))
	status = forms.ChoiceField(choices = CHOICES)
	location = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder':'Storage Location'}))
  
	# checks if status is in bank and raises validation error if no location is input
	def clean(self):
		cd = self.cleaned_data

		if cd.get('status') == "In Bank" and cd.get('location') == "":
			raise forms.ValidationError('Location can not be blank when status is In Bank') 
		return cd
