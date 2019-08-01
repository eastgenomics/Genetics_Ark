# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.views.generic.edit import FormView
from django.contrib import messages
from django.views.generic import  ListView
from .tables import PrimerDetailsTable
from django_tables2 import RequestConfig
from django.forms.models import model_to_dict

#from django_tables2.views import SingleTableMixin
#from django_filters.views import FilterView
#import django_filters
import primer_db.forms as Forms
import primer_db.models as Models





def submit(request):
    template = loader.get_template('primer_db/submit.html')
   # return render(request, 'primer_db/index.html')

    context_dict = {}

    if request.method == "POST":
            # data is sent
        primer_name_form = Forms.PrimerNameForm(request.POST)
        sequence_form = Forms.SequenceForm(request.POST)
        status_form = Forms.StatusForm(request.POST)
        gcpercent_form = Forms.GCPercentForm(request.POST)
        tm_form = Forms.TMForm(request.POST)
        length_form = Forms.LengthForm(request.POST)
        comments_form = Forms.CommentsForm(request.POST)
        arrival_date_form = Forms.ArrivalDateForm(request.POST)
        buffer_form = Forms.BufferForm(request.POST)
        pcr_form = Forms.PCRForm(request.POST)
        forename_form = Forms.ScientistForenameForm(request.POST)
        surname_form = Forms.ScientistSurnameForm(request.POST)
        reference_form = Forms.ReferenceForm(request.POST)
        chrom_no_form = Forms.ChromNoForm(request.POST)
        start_coordinate_37_form = Forms.StartCoordinateForm(request.POST)
        end_coordinate_37_form = Forms.EndCoordinateForm(request.POST)




        if (primer_name_form.is_valid() and 
            sequence_form.is_valid() and
            status_form.is_valid() and
            gcpercent_form.is_valid() and
            tm_form.is_valid() and
            length_form.is_valid() and
            comments_form.is_valid() and
            arrival_date_form.is_valid() and
            buffer_form.is_valid() and
            pcr_form.is_valid() and
            forename_form.is_valid() and
            surname_form.is_valid() and
            reference_form.is_valid() and
            chrom_no_form.is_valid() and
            start_coordinate_37_form.is_valid() and
            end_coordinate_37_form.is_valid()
            ):

            # the form is valid
            primer_name = primer_name_form.cleaned_data["primer_name"] 
            print(primer_name)
            sequence = sequence_form.cleaned_data["sequence"]
            print(sequence)
            status = status_form.cleaned_data["status"]
            print(status)
            gc_percent = gcpercent_form.cleaned_data["gc_percent"]
            print(gc_percent)
            tm = tm_form.cleaned_data["tm"]
            print(tm)
            length = length_form.cleaned_data["length"]
            print(length)
            comments = comments_form.cleaned_data["comments"]
            print(comments)
            arrival_date = arrival_date_form.cleaned_data["arrival_date"]
            print(arrival_date)
            buffer = buffer_form.cleaned_data["buffer"].capitalize()
            print(buffer)
            pcr_program = pcr_form.cleaned_data["pcr_program"]
            print(pcr_program)
            forename = forename_form.cleaned_data["forename"].capitalize()
            print(forename)
            surname = surname_form.cleaned_data["surname"].capitalize()
            print(surname)
            reference = reference_form.cleaned_data["reference"]
            print(reference)
            chrom_no = chrom_no_form.cleaned_data["chrom_no"]
            print(chrom_no)
            start_coordinate_37 = start_coordinate_37_form.cleaned_data["start_coordinate_37"]
            print(start_coordinate_37)
            end_coordinate_37 = end_coordinate_37_form.cleaned_data["end_coordinate_37"]
            print(end_coordinate_37)


            print(status)

            # save primer to database
            
            new_status, created = Models.Status.objects.get_or_create(status = status)
            print(new_status)
            new_scientist, created = Models.Scientist.objects.get_or_create(
                forename = forename, surname = surname)
            new_pcr, created = Models.PCRProgram.objects.get_or_create(
                pcr_program = pcr_program)
            print(new_pcr)
            new_buffer, created = Models.Buffer.objects.get_or_create(buffer = buffer)
            print(new_buffer)
            new_coordinates, created = Models.Coordinates.objects.get_or_create(
                start_coordinate_37 = start_coordinate_37, end_coordinate_37 = end_coordinate_37,
                reference = reference, chrom_no = chrom_no
                )
            print(new_coordinates)  


            new_primer =  Models.PrimerDetails.objects.create(
                primer_name = primer_name, sequence = sequence, 
                gc_percent = gc_percent, tm = tm, length = length,
                comments =  comments, arrival_date = arrival_date,
                status = new_status, scientist = new_scientist,
                pcr_program = new_pcr, buffer = new_buffer,
                coordinates = new_coordinates)

            primer = Models.PrimerDetails.objects.filter(primer_name__icontains = primer_name)
            context_dict["primer"] = primer
            messages.success(request, 'Primers successfully saved')
        


            # recreate the form
            primer_name_form = Forms.PrimerNameForm()
            sequence_form = Forms.SequenceForm()
            status_form = Forms.StatusForm()
            gcpercent_form = Forms.GCPercentForm()
            tm_form = Forms.TMForm()
            length_form = Forms.LengthForm()
            comments_form = Forms.CommentsForm()
            arrival_date_form = Forms.ArrivalDateForm()
            buffer_form = Forms.BufferForm()
            pcr_form = Forms.PCRForm()
            forename_form = Forms.ScientistForenameForm()
            surname_form = Forms.ScientistSurnameForm()
            reference_form = Forms.ReferenceForm()
            chrom_no_form = Forms.ChromNoForm()
            start_coordinate_37_form = Forms.StartCoordinateForm()
            end_coordinate_37_form = Forms.EndCoordinateForm()


            context_dict["primer_name_form"] = primer_name_form
            context_dict["sequence_form"] = sequence_form
            context_dict["status_form"] = status_form
            context_dict["gcpercent_form"] = gcpercent_form
            context_dict["tm_form"] = tm_form
            context_dict["length_form"] = length_form
            context_dict["comments_form"] = comments_form
            context_dict["arrival_date_form"] = arrival_date_form
            context_dict["buffer_form"] = buffer_form
            context_dict["pcr_form"] = pcr_form
            context_dict["forename_form"] = forename_form
            context_dict["surname_form"] = surname_form
            context_dict["reference_form"] = reference_form
            context_dict["chrom_no_form"] = chrom_no_form
            context_dict["start_coordinate_37_form"] = start_coordinate_37_form
            context_dict["end_coordinate_37_form"] = end_coordinate_37_form

                # return the page with the new comment
            return render(request, 'primer_db/submit.html', context_dict)

    else:
            # if data is not sent, just display the form
        primer_name_form = Forms.PrimerNameForm()
        sequence_form = Forms.SequenceForm()
        status_form = Forms.StatusForm()
        gcpercent_form = Forms.GCPercentForm()
        tm_form = Forms.TMForm()
        length_form = Forms.LengthForm()
        comments_form = Forms.CommentsForm()
        arrival_date_form = Forms.ArrivalDateForm()
        buffer_form = Forms.BufferForm()
        pcr_form = Forms.PCRForm()
        forename_form = Forms.ScientistForenameForm()
        surname_form = Forms.ScientistSurnameForm()
        reference_form = Forms.ReferenceForm()
        chrom_no_form = Forms.ChromNoForm()
        start_coordinate_37_form = Forms.StartCoordinateForm()
        end_coordinate_37_form = Forms.EndCoordinateForm()
            
    context_dict["primer_name_form"] = primer_name_form
    context_dict["sequence_form"] = sequence_form
    context_dict["status_form"] = status_form
    context_dict["gcpercent_form"] = gcpercent_form
    context_dict["tm_form"] = tm_form
    context_dict["length_form"] = length_form
    context_dict["comments_form"] = comments_form
    context_dict["arrival_date_form"] = arrival_date_form
    context_dict["buffer_form"] = buffer_form
    context_dict["pcr_form"] = pcr_form
    context_dict["forename_form"] = forename_form
    context_dict["surname_form"] = surname_form
    context_dict["reference_form"] = reference_form
    context_dict["chrom_no_form"] = chrom_no_form
    context_dict["start_coordinate_37_form"] = start_coordinate_37_form
    context_dict["end_coordinate_37_form"] = end_coordinate_37_form


    return render(request, 'primer_db/submit.html', context_dict)



    
def index(request):

    context_dict = {}
    table = PrimerDetailsTable(Models.PrimerDetails.objects.all())
 
    context_dict["table"] = table

    # function for filtering primers by variant position within coordinates
    if request.method == 'GET':

        var_pos = request.GET.get('var_pos', None)
        
        if var_pos:
            primers = Models.PrimerDetails.objects.filter(coordinates__start_coordinate_37__lte=var_pos, 
                coordinates__end_coordinate_37__gte=var_pos)
            context_dict["primers"] = primers
            print(primers)

            table = PrimerDetailsTable(primers)
            RequestConfig(request, paginate={'per_page': 50}).configure(table)

            context_dict["table"] = table

            return render(request, 'primer_db/index.html', context_dict)

    else:
        print("none")

    # function for filtering primers by part of name
    if request.method == 'GET':

        name_filter = request.GET.get('name_filter', None)
        
        if name_filter:
            primer_names = Models.PrimerDetails.objects.filter(primer_name__icontains=name_filter)
            context_dict["primer_names"] = primer_names
            print(primer_names)

            table = PrimerDetailsTable(primer_names)
            RequestConfig(request, paginate={'per_page': 50}).configure(table)

            context_dict["table"] = table

            return render(request, 'primer_db/index.html', context_dict)


    else:
        print("none")

    RequestConfig(request, paginate={'per_page': 50}).configure(table)

    return render(request, 'primer_db/index.html', context_dict)




def edit_primer(request, PrimerDetails_id):

    context_dict = {}

    print(PrimerDetails_id)

    primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)

    primer = primer[0]
    buffer = primer.buffer
    scientist = primer.scientist
    pcr_program = primer.pcr_program
    coordinates = primer.coordinates


    primer_name_form = Forms.PrimerNameForm(initial = model_to_dict(primer))
    sequence_form = Forms.SequenceForm(initial = model_to_dict(primer))
    status_form = Forms.StatusForm(initial = model_to_dict(primer))
    gcpercent_form = Forms.GCPercentForm(initial = model_to_dict(primer))
    tm_form = Forms.TMForm(initial = model_to_dict(primer))
    length_form = Forms.LengthForm(initial = model_to_dict(primer))
    comments_form = Forms.CommentsForm(initial = model_to_dict(primer))
    arrival_date_form = Forms.ArrivalDateForm(initial = model_to_dict(primer))
    buffer_form = Forms.BufferForm(initial = model_to_dict(buffer))
    pcr_form = Forms.PCRForm(initial = model_to_dict(pcr_program))
    forename_form = Forms.ScientistForenameForm(initial = model_to_dict(scientist))
    surname_form = Forms.ScientistSurnameForm(initial = model_to_dict(scientist))
    reference_form = Forms.ReferenceForm(initial = model_to_dict(coordinates))
    chrom_no_form = Forms.ChromNoForm(initial = model_to_dict(coordinates))
    start_coordinate_37_form = Forms.StartCoordinateForm(initial = model_to_dict(coordinates))
    end_coordinate_37_form = Forms.EndCoordinateForm(initial = model_to_dict(coordinates))


    context_dict["primer_name_form"] = primer_name_form
    context_dict["sequence_form"] = sequence_form
    context_dict["status_form"] = status_form
    context_dict["gcpercent_form"] = gcpercent_form
    context_dict["tm_form"] = tm_form
    context_dict["length_form"] = length_form
    context_dict["comments_form"] = comments_form
    context_dict["arrival_date_form"] = arrival_date_form
    context_dict["buffer_form"] = buffer_form
    context_dict["pcr_form"] = pcr_form
    context_dict["forename_form"] = forename_form
    context_dict["surname_form"] = surname_form
    context_dict["reference_form"] = reference_form
    context_dict["chrom_no_form"] = chrom_no_form
    context_dict["start_coordinate_37_form"] = start_coordinate_37_form
    context_dict["end_coordinate_37_form"] = end_coordinate_37_form

    context_dict["primer"] = primer


    return render(request, 'primer_db/edit_primer.html', context_dict)
    

    if request.method == "POST":
            # data is sent
        primer_name_form = Forms.PrimerNameForm(request.POST)
        sequence_form = Forms.SequenceForm(request.POST)
        status_form = Forms.StatusForm(request.POST)
        gcpercent_form = Forms.GCPercentForm(request.POST)
        tm_form = Forms.TMForm(request.POST)
        length_form = Forms.LengthForm(request.POST)
        comments_form = Forms.CommentsForm(request.POST)
        arrival_date_form = Forms.ArrivalDateForm(request.POST)
        buffer_form = Forms.BufferForm(request.POST)
        pcr_form = Forms.PCRForm(request.POST)
        forename_form = Forms.ScientistForenameForm(request.POST)
        surname_form = Forms.ScientistSurnameForm(request.POST)
        reference_form = Forms.ReferenceForm(request.POST)
        chrom_no_form = Forms.ChromNoForm(request.POST)
        start_coordinate_37_form = Forms.StartCoordinateForm(request.POST)
        end_coordinate_37_form = Forms.EndCoordinateForm(request.POST)



        if (primer_name_form.is_valid() and 
            sequence_form.is_valid() and
            status_form.is_valid() and
            gcpercent_form.is_valid() and
            tm_form.is_valid() and
            length_form.is_valid() and
            comments_form.is_valid() and
            arrival_date_form.is_valid() and
            buffer_form.is_valid() and
            pcr_form.is_valid() and
            forename_form.is_valid() and
            surname_form.is_valid() and
            reference_form.is_valid() and
            chrom_no_form.is_valid() and
            start_coordinate_37_form.is_valid() and
            end_coordinate_37_form.is_valid()
            ):

            # the form is valid
            primer_name = primer_name_form.cleaned_data["primer_name"] 
            print(primer_name)
            sequence = sequence_form.cleaned_data["sequence"]
            print(sequence)
            status = status_form.cleaned_data["status"]
            print(status)
            gcpercent = gcpercent_form.cleaned_data["gcpercent"]
            print(gcpercent)
            tm = tm_form.cleaned_data["tm"]
            print(tm)
            length = length_form.cleaned_data["length"]
            print(length)
            comments = comments_form.cleaned_data["comments"]
            print(comments)
            arrival_date = arrival_date_form.cleaned_data["arrival_date"]
            print(arrival_date)
            buffer = buffer_form.cleaned_data["buffer"].capitalize()
            print(buffer)
            pcr_program = pcr_form.cleaned_data["pcr_program"]
            print(pcr_program)
            forename = forename_form.cleaned_data["forename"].capitalize()
            print(forename)
            surname = surname_form.cleaned_data["surname"].capitalize()
            print(surname)
            reference = reference_form.cleaned_data["reference"]
            print(reference)
            chrom_no = chrom_no_form.cleaned_data["chrom_no"]
            print(chrom_no)
            start_coordinate_37 = start_coordinate_37_form.cleaned_data["start_coordinate_37"]
            print(start_coordinate_37)
            end_coordinate_37 = end_coordinate_37_form.cleaned_data["end_coordinate_37"]
            print(end_coordinate_37)


            print(saving_status)

            # save primer to database
            
            new_status, created = Models.Status.objects.get_or_create(status = status)
            print(new_status)
            new_scientist, created = Models.Scientist.objects.get_or_create(
                forename = forename, surname = surname)
            new_pcr, created = Models.PCRProgram.objects.get_or_create(
                pcr_program = pcr_program)
            print(new_pcr)
            new_buffer, created = Models.Buffer.objects.get_or_create(buffer = buffer)
            print(new_buffer)
            new_coordinates, created = Models.Coordinates.objects.get_or_create(
                start_coordinate_37 = start_coordinate_37, end_coordinate_37 = end_coordinate_37,
                reference = reference, chrom_no = chrom_no
                )
            print(new_coordinates)  


            new_primer =  Models.PrimerDetails.objects.create(
                primer_name = primer_name, sequence = sequence, 
                gc_percent = gcpercent, tm = tm, length = length,
                comments =  comments, arrival_date = arrival_date,
                status = new_status, scientist = new_scientist,
                pcr_program = new_pcr, buffer = new_buffer,
                coordinates = new_coordinates)

            primer = Models.PrimerDetails.objects.filter(primer_name__icontains = primer_name)
            context_dict["primer"] = primer
            messages.success(request, 'Primers successfully updated')