from django import forms
from django.forms import ModelForm
from datetime import datetime
from .models import PrimerDetails, Coordinates, Status, Scientist, PCRProgram, Buffer 
from django.core.exceptions import ValidationError

class PrimerForm(forms.Form):
	name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter primer name'}))
	gene = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter gene name'}))
	# gc_percent = forms.FloatField(widget=forms.TextInput(attrs={'placeholder':'Enter GC %', 'autocomplete': 'off'}))
	# tm = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter melting temp', 'autocomplete': 'off'}))
	comments = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder':'Other comments'}))
	buffer = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Buffer'}), initial="Buffer D")
	pcr_program = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'PCR Program'}), initial = "TD65_55")	
	forename = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Scientist Forename'}))
	surname = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Scientist Surname'}))


class SequenceForm(forms.Form):
	sequence = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter primer sequence', 'autocomplete': 'off'}))


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


class SNPForm(forms.Form):
	snp_status = forms.CharField(required=False)
	snp_info = forms.CharField(required=False)
	snp_date = forms.DateField()			


class ReferenceForm(forms.Form):
	ref_choice = (('37', '37'), ('38', '38'))
	reference = forms.ChoiceField(choices = ref_choice)	


class ChromNoForm(forms.Form):
	chrom_choice = (('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), 
				('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'), ('13', '13'), 
				('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), 
				('20', '20'), ('21', '21'), ('22', '22'), ('23', '23'), ('X', 'X'), ('Y', 'Y'))
	chrom_no = forms.ChoiceField(choices = chrom_choice)


class SubmitCoordinateForm(forms.Form):
	start_coordinate = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Start coordinate', 'autocomplete': 'off'}))
	end_coordinate = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'End coordinate', 'autocomplete': 'off'}))


class CoordinateForm(forms.Form):
	start_coordinate_37 = forms.IntegerField(required=False, widget=forms.TextInput(
		attrs={'placeholder':'Start coordinate', 'autocomplete': 'off'}))
	end_coordinate_37 = forms.IntegerField(required=False, widget=forms.TextInput(
		attrs={'placeholder':'End coordinate', 'autocomplete': 'off'}))
	start_coordinate_38 = forms.IntegerField(required=False, widget=forms.TextInput(
		attrs={'placeholder':'Start coordinate', 'autocomplete': 'off'}))
	end_coordinate_38 = forms.IntegerField(required=False, widget=forms.TextInput(
		attrs={'placeholder':'End coordinate', 'autocomplete': 'off'}))


class CoverageForm(forms.Form):
	coverage_37 = forms.CharField(required=False, widget=forms.TextInput)
	coverage_38 = forms.CharField(required=False, widget=forms.TextInput)