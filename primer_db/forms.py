from django import forms
from django.forms import ModelForm
import datetime
from .models import PrimerDetails, Coordinates, Status, Scientist, PCRProgram, Buffer 


class PrimerNameForm(forms.Form):
	primer_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter primer name'}))

	# def clean(self):
	# 	if "add" in self.data:
	# 		print("add")
	# 	elif "search" in self.data:
	# 		print("search")

class SequenceForm(forms.Form):
	sequence = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter primer sequence', 'autocomplete': 'off'}))

class GCPercentForm(forms.Form):
	gc_percent = forms.FloatField(widget=forms.TextInput(attrs={'placeholder':'Enter GC %', 'autocomplete': 'off'}))

class TMForm(forms.Form):
	tm = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter melting temp', 'autocomplete': 'off'}))

class LengthForm(forms.Form):
	length = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Enter sequence length', 'autocomplete': 'off'}))

class CommentsForm(forms.Form):
	comments = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder':'Other comments'}))

class ArrivalDateForm(forms.Form):
	arrival_date = forms.DateField(widget=forms.SelectDateWidget, initial=datetime.date.today)

class StatusForm(forms.Form):
	CHOICES = (('On order', 'On order'), ('In Bank', 'In Bank'), ('Archived', 'Archived'))
	status = forms.ChoiceField(choices = CHOICES)
	
class BufferForm(forms.Form):
	buffer = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Buffer'}), initial="Buffer D")

class PCRForm(forms.Form):
	pcr_program = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'PCR Program'}))

class ScientistForenameForm(forms.Form):
	forename = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Scientist Forename'}))

class ScientistSurnameForm(forms.Form):
	surname = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Scientist Surname'}))

class ReferenceForm(forms.Form):
	CHOICES = (('37', '37'), ('38', '38'))
	reference = forms.ChoiceField(choices = CHOICES)	

class ChromNoForm(forms.Form):
	# chrom_no = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Chromosome no.'}))
	CHOICES = (('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), 
				('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'), ('13', '13'), 
				('14', '14'), ('15', '15'), ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), 
				('20', '20'), ('21', '21'), ('22', '22'), ('23', '23'), ('X', 'X'), ('Y', 'Y'))
	chrom_no = forms.ChoiceField(choices=CHOICES)

class StartCoordinateForm(forms.Form):
	start_coordinate = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'Start coordinate', 'autocomplete': 'off'}))

class EndCoordinateForm(forms.Form):
	end_coordinate = forms.CharField(widget=forms.TextInput(attrs={'placeholder':'End coordinate', 'autocomplete': 'off'}))
	
class StartCoordinate37Form(forms.Form):
	start_coordinate_37 = forms.IntegerField(widget=forms.TextInput(attrs={'placeholder':'Start coordinate', 'autocomplete': 'off'}))

class EndCoordinate37Form(forms.Form):
	end_coordinate_37 = forms.IntegerField(widget=forms.TextInput(attrs={'placeholder':'End coordinate', 'autocomplete': 'off'}))

class StartCoordinate38Form(forms.Form):
	start_coordinate_38 = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'placeholder':'Start coordinate', 'autocomplete': 'off'}))

class EndCoordinate38Form(forms.Form):
	end_coordinate_38 = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'placeholder':'End coordinate', 'autocomplete': 'off'}))