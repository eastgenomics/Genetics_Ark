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


class CommentForm(forms.Form):
    comment = forms.CharField(required = False, widget = forms.Textarea)

class SearchDeconGeneForm(forms.Form):
    decongene = forms.CharField(help_text = "Enter a gene name", widget = forms.TextInput)

    def clean_decongene(self): 
        name = self.cleaned_data['decongene']

        if re.match("^[a-zA-Z0-9]*$", name):
            name = name.strip().upper()

        else: 
            raise forms.ValidationError("Invalid gene name, should not contain special characters!")

        return name

