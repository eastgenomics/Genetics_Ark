from django import forms
from django.forms import ModelForm
from datetime import datetime
from .models import PrimerDetails, Coordinates, Status, Scientist, PCRProgram, Buffer 
from django.core.exceptions import ValidationError

import re

class PrimerForm(forms.Form):
	name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter primer name'}))
	gene = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter gene name'}))
	comments = forms.CharField(required=False, widget=forms.Textarea(attrs={'placeholder':'Other comments', "cols": 50}))
	buffer = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Buffer'}), initial="Buffer D")
	pcr_program = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'PCR Program'}), initial = "TD65_55")	
	forename = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Scientist Forename'}))
	surname = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Scientist Surname'}))


class SequenceForm(forms.Form):
	sequence = forms.CharField(widget=forms.Textarea(attrs={
		'placeholder':'Enter primer sequence',
		'autocomplete': 'off', "rows": 1, "cols": 50}))

	def clean(self):
		data = self.cleaned_data["sequence"]

		for nucl in data:
			nucl = nucl.upper()

			if nucl not in ["A", "T", "C", "G"]:
				raise forms.ValidationError("Nucleotide sequence cannot contain anything other than ATCG")

		return self.cleaned_data


class ArrivalDateForm(forms.Form):
	this_year = datetime.now().year
	arrival_date = forms.DateField(widget=forms.SelectDateWidget(years=range(this_year - 5,this_year + 3)), 
		initial=datetime.now)

class DateLastUsedForm(forms.Form):
	this_year = datetime.now().year
	date_last_used = forms.DateField(widget=forms.SelectDateWidget(years=range(this_year - 5,this_year + 3)), 
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

class FilterForm(forms.Form):
	name = forms.CharField(required = False, widget=forms.TextInput(attrs={'placeholder':'Filter by primer name'}))
	gene = forms.CharField(required = False, widget=forms.TextInput(attrs={'placeholder':'Filter by gene'}))
	location = forms.CharField(required = False, widget=forms.TextInput(attrs={'placeholder':'Filter by storage location'}))
	status = forms.ChoiceField(required = False, choices = (
		("", "Filter by status"),
		("On order", "On order"),
		("In Bank", "In Bank"),
		("Archived", "Archived")
	))
	chrom = forms.CharField(required = False, widget=forms.TextInput(attrs={'placeholder':'Filter by chrom'}))
	position = forms.IntegerField(required = False, min_value=1, widget=forms.TextInput(attrs={'placeholder':'Filter by genomic position'}))

	def clean(self):
		cd = self.cleaned_data

		for field, value in cd.items():
			if value:
				if field == "gene":
					if re.search(r"[^0-9a-zA-Z]", value):
						raise ValidationError("Gene symbol cannot contain non alphanumerical characters")

				elif field == "chrom":
					if value.isdigit():
						value = int(value)
						
						if 1 >= value >= 22:
							raise ValidationError("Chrom can't be under 1 or over 22 (at least in the human)")
					
					else:
						if re.search(r"[^xyXY]", value):
							raise ValidationError("Chrom can't be a character other than \"X\" or \"Y\"")
				
				elif field == "position":
					if value < 1:
						raise ValidationError("Genomic position can't be under 1")
