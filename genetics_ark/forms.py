from django import forms
from django.forms import ModelForm
from django.forms import formset_factory

import genetics_ark.models as Models

import re
import pprint as pp


class PanelForm( forms.Form ):
    
    class PanelModelChoiceField( forms.ModelChoiceField ):
        def label_from_instance(self, obj):
            if ( obj.ext_id ):
                return "%s (%d)" % (obj.name, obj.ext_id)
            else:
                return "%s" % obj.name

    class GeneModelChoiceField( forms.ModelChoiceField ):
        def label_from_instance(self, obj):
            if ( obj.id ):
                return "{} ({})".format(obj.gene.name, obj.refseq)
            else:
                return "%s" % obj.name

    panel = PanelModelChoiceField(queryset= Models.Panel.objects.filter(active = "Y").order_by('name'), to_field_name='id', label=False, required=False )
    gene  = GeneModelChoiceField(queryset= Models.Transcript.objects.filter( clinical_transcript = 'Y').order_by('gene__name'), to_field_name='id', label=False, required=False )
    selected_panels = forms.CharField(required=False)
    selected_transcripts  = forms.CharField(required=False)


class UserForm(forms.Form):
    user = forms.CharField(widget = forms.TextInput(attrs={'placeholder':'Enter your name'}))


class CommentForm(forms.Form):
    comment = forms.CharField(widget = forms.Textarea(attrs={'placeholder':'Enter your comment'}))


class SearchGeneForm(forms.Form):
    gene = forms.CharField(widget = forms.TextInput(attrs={'placeholder': 'e.g. BRCA1'}), required = False)

    def clean(self):
        name = self.cleaned_data['gene']

        if name:
            if re.match("^[a-zA-Z0-9]*$", name):
                name = name.strip().upper()

            else:
                raise forms.ValidationError("Invalid gene name, should not contain special characters!")

        return name


class SearchSampleForm(forms.Form):
    sample = forms.CharField(widget = forms.TextInput(attrs={'placeholder': 'e.g. X007321'}), required = False)

    def clean(self):
        sample_name = self.cleaned_data['sample']

        if sample_name:
            if re.match("^[a-zA-Z0-9]*$", sample_name):
                sample_name = sample_name.strip().upper()

            else:
                raise forms.ValidationError("Invalid gene name, should not contain special characters!")

        return sample_name

    
class SearchPositionForm(forms.Form):
    position = forms.CharField(widget = forms.TextInput(attrs={'placeholder':'e.g. chrom:start-stop'}), required = False)

    def clean(self):
        position = self.cleaned_data['position']

        if position:
            if (":" in position and "-" not in position) or (":" not in position and "-" in position):
                raise forms.ValidationError("Invalid input: not respecting the right format for entering genomic coordinates e.g. chrom:start-stop")

            elif " " in position:
                position = position.split()
                chrom = position[0]
                start = position[1]
                stop  = position[2]

            elif ":" in position and "-" in position:
                chrom = position.split(":")[0]
                start = position.split(":")[1].split("-")[0]
                stop = position.split(":")[1].split("-")[1]

            else:
                raise forms.ValidationError('Invalid input: not respecting the right format for entering genomic coordinates e.g. chrom:start-stop')

            try:
                start = int(start)
                stop = int(stop)
            except:
                raise forms.ValidationError("Invalid input: start \"{}\" or stop \"{}\" not numbers".format(start, stop))

            if start > stop:
                raise forms.ValidationError('Invalid value: start \"{}\" > stop \"{}\"'.format(start, stop))

            return (chrom, start, stop)

        else:
            position = ""
            return position
        