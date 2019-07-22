# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse
from django.template import loader
from django.views.generic.edit import FormView

import primer_db.forms as Forms
import primer_db.models as Models




def index(request):
    template = loader.get_template('primer_db/index.html')
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
        start_coordinate_form = Forms.StartCoordinateForm(request.POST)
        end_coordinate_form = Forms.EndCoordinateForm(request.POST)

        print("status1")



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
            start_coordinate_form.is_valid() and
            end_coordinate_form.is_valid()
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
            start_coordinate = start_coordinate_form.cleaned_data["start_coordinate"]
            print(start_coordinate)
            end_coordinate = end_coordinate_form.cleaned_data["end_coordinate"]
            print(end_coordinate)


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
                start_coordinate = start_coordinate, end_coordinate = end_coordinate,
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
            start_coordinate_form = Forms.StartCoordinateForm()
            end_coordinate_form = Forms.EndCoordinateForm()


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
            context_dict["start_coordinate_form"] = start_coordinate_form
            context_dict["end_coordinate_form"] = end_coordinate_form

                # return the page with the new comment
            return render(request, 'primer_db/index.html', context_dict)

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
        start_coordinate_form = Forms.StartCoordinateForm()
        end_coordinate_form = Forms.EndCoordinateForm()
            
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
    context_dict["start_coordinate_form"] = start_coordinate_form
    context_dict["end_coordinate_form"] = end_coordinate_form


    return render(request, 'primer_db/index.html', context_dict)

