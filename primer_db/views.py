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
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import ValidationError


import primer_db.forms as Forms
import primer_db.models as Models


# function for submitting new primers to database
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
        start_coordinate_form = Forms.StartCoordinateForm(request.POST)
        end_coordinate_form = Forms.EndCoordinateForm(request.POST)
        #location_form = Forms.LocationForm(request.POST)



        # check if data input to each form is valid
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
            #location_form.is_valid()
            ):


            # the form is valid
            primer_name = primer_name_form.cleaned_data["primer_name"] 
            sequence = sequence_form.cleaned_data["sequence"]
            status = status_form.cleaned_data["status"]
            gc_percent = gcpercent_form.cleaned_data["gc_percent"]
            tm = tm_form.cleaned_data["tm"]
            length = length_form.cleaned_data["length"]
            comments = comments_form.cleaned_data["comments"]
            arrival_date = arrival_date_form.cleaned_data["arrival_date"]
            buffer = buffer_form.cleaned_data["buffer"].capitalize()
            pcr_program = pcr_form.cleaned_data["pcr_program"]
            forename = forename_form.cleaned_data["forename"].capitalize()
            surname = surname_form.cleaned_data["surname"].capitalize()
            reference = reference_form.cleaned_data["reference"]
            chrom_no = chrom_no_form.cleaned_data["chrom_no"]
            location = status_form.cleaned_data["location"]


        

            # checks if ref 37 or 38 has been selected and selects appropriate database field
            if reference == "37":

                start_coordinate_37 = start_coordinate_form.cleaned_data["start_coordinate"]
                end_coordinate_37 = end_coordinate_form.cleaned_data["end_coordinate"]
                start_coordinate_38 = None
                end_coordinate_38 = None

            elif reference == "38":   

                start_coordinate_38 = start_coordinate_form.cleaned_data["start_coordinate"]
                end_coordinate_38 = end_coordinate_form.cleaned_data["end_coordinate"]
                start_coordinate_37 = None
                end_coordinate_37 = None

            else:
                pass # needs something here although it can only be 37 or 38 since it is a choicefield


            # save primer to database
            
            new_status, created = Models.Status.objects.get_or_create(status = status)

            new_scientist, created = Models.Scientist.objects.get_or_create(
                forename = forename, surname = surname)

            new_pcr, created = Models.PCRProgram.objects.get_or_create(
                pcr_program = pcr_program)

            new_buffer, created = Models.Buffer.objects.get_or_create(buffer = buffer)

            new_coordinates, created = Models.Coordinates.objects.get_or_create(
                start_coordinate_37 = start_coordinate_37, end_coordinate_37 = end_coordinate_37,
                start_coordinate_38 = start_coordinate_38, end_coordinate_38 = end_coordinate_38,
                reference = reference, chrom_no = chrom_no
                )

            new_primer =  Models.PrimerDetails.objects.create(
                primer_name = primer_name, sequence = sequence, 
                gc_percent = gc_percent, tm = tm, length = length,
                comments =  comments, arrival_date = arrival_date,
                location = location,status = new_status, 
                scientist = new_scientist,pcr_program = new_pcr, 
                buffer = new_buffer, coordinates = new_coordinates)

            # success save message passed to submit.html
            messages.success(request, 'Primers successfully saved')
        


            # recreate the empty form
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
            #location_form = Forms.LocationForm()


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
            #context_dict["locatio=_form"] = location_form


            # return the submit page
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
        start_coordinate_form = Forms.StartCoordinateForm()
        end_coordinate_form = Forms.EndCoordinateForm()
        #location_form = Forms.LocationForm()

            
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
    #context_dict["location_form"] = location_form

    return render(request, 'primer_db/submit.html', context_dict)



# homepage view of database, displays all primers and inc. search functions    
def index(request):

    context_dict = {}
    table = PrimerDetailsTable(Models.PrimerDetails.objects.all())

    # returns primer totals filtered by status for displaying on main db view
    total_archived = Models.PrimerDetails.objects.filter(status__status__icontains="archived").count()
    total_bank = Models.PrimerDetails.objects.filter(status__status__icontains="bank").count()
    total_order = Models.PrimerDetails.objects.filter(status__status__icontains="order").count()

    context_dict["table"] = table
    context_dict["total_archived"] = total_archived
    context_dict["total_bank"] = total_bank
    context_dict["total_order"] = total_order



    # function for filtering primers by variant position within coordinates 
    # needs also filtering by chromosome number 
    if request.method == 'GET':

        var_pos = request.GET.get('var_pos', None)
        chrom_no = request.GET.get('chrom_no', None)
        
        context_dict["var_pos"] = var_pos
        context_dict["chrom_no"] = chrom_no

        if var_pos:
            
            primers37 = Models.PrimerDetails.objects.filter(coordinates__start_coordinate_37__lte=var_pos, 
                coordinates__end_coordinate_37__gte=var_pos).filter(coordinates__chrom_no=chrom_no)
            primers38 = Models.PrimerDetails.objects.filter(coordinates__start_coordinate_38__lte=var_pos, 
                coordinates__end_coordinate_38__gte=var_pos).filter(coordinates__chrom_no=chrom_no)

            #chrom_no = Models.PrimerDetails.objects.filter(coordinates__chrom_no=chrom_no)


            #context_dict["chrom_no"] = chrom_no
            context_dict["37_primers"] = primers37
            context_dict["38_primers"] = primers38

            table = PrimerDetailsTable(primers37, primers38)
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

        pass
        print("searching passed")

    RequestConfig(request, paginate={'per_page': 30}).configure(table)

    return render(request, 'primer_db/index.html', context_dict)



# function for edit_primer view of individual primers
def edit_primer(request, PrimerDetails_id):

    context_dict = {}

    if request.method == "POST":
        print("pressed")

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
        start_coordinate_37_form = Forms.StartCoordinate37Form(request.POST)
        end_coordinate_37_form = Forms.EndCoordinate37Form(request.POST)
        start_coordinate_38_form = Forms.StartCoordinate38Form(request.POST)
        end_coordinate_38_form = Forms.EndCoordinate38Form(request.POST)



        # when update button is pressed, save updates made to current primer
        if request.POST.get("update_primer"):
            print("update button pressed")
            # checks the form is valid
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
                chrom_no_form.is_valid() and
                start_coordinate_37_form.is_valid() and
                end_coordinate_37_form.is_valid() and
                start_coordinate_38_form.is_valid() and
                end_coordinate_38_form.is_valid() 
                ):
                print("update form is valid")
                # the form is valid
                primer_name = primer_name_form.cleaned_data["primer_name"] 
                sequence = sequence_form.cleaned_data["sequence"]
                status = status_form.cleaned_data["status"]
                gcpercent = gcpercent_form.cleaned_data["gc_percent"]
                tm = tm_form.cleaned_data["tm"]
                length = length_form.cleaned_data["length"]
                comments = comments_form.cleaned_data["comments"]
                arrival_date = arrival_date_form.cleaned_data["arrival_date"]
                buffer = buffer_form.cleaned_data["buffer"].capitalize()
                pcr_program = pcr_form.cleaned_data["pcr_program"]
                forename = forename_form.cleaned_data["forename"].capitalize()
                surname = surname_form.cleaned_data["surname"].capitalize()
                chrom_no = chrom_no_form.cleaned_data["chrom_no"]
                start_coordinate_37 = start_coordinate_37_form.cleaned_data["start_coordinate_37"]
                end_coordinate_37 = end_coordinate_37_form.cleaned_data["end_coordinate_37"]
                start_coordinate_38 = start_coordinate_38_form.cleaned_data["start_coordinate_38"]
                end_coordinate_38 = end_coordinate_38_form.cleaned_data["end_coordinate_38"]
                location = status_form.cleaned_data["location"]


                # save primer to database
                print("saving")
                new_status, created = Models.Status.objects.update_or_create(status = status)

                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                new_pcr, created = Models.PCRProgram.objects.update_or_create(
                    pcr_program = pcr_program)

                new_buffer, created = Models.Buffer.objects.update_or_create(buffer = buffer)

                new_coordinates, created = Models.Coordinates.objects.update_or_create(
                    start_coordinate_37 = start_coordinate_37, end_coordinate_37 = end_coordinate_37,
                    start_coordinate_38 = start_coordinate_38, end_coordinate_38 = end_coordinate_38,
                    chrom_no = chrom_no
                    )

                # if primer is present updates, if not creates new instance in database
                new_primer =  Models.PrimerDetails.objects.update_or_create(
                    primer_name = primer_name, 
                    defaults={
                    'sequence': sequence, 
                    'gc_percent': gcpercent, 'tm': tm, 'length': length,
                    'comments':  comments, 'arrival_date': arrival_date,
                    'location': location, 'status': new_status, 
                    'scientist': new_scientist,'pcr_program': new_pcr, 
                    'buffer': new_buffer, 'coordinates': new_coordinates})

                #messages.success(request, 'Primer successfully updated')


                primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)

                #new_primer = new_primer[0]
            
                updated_primer = primer[0].primer_name

                messages.success(request, 'Primer "{primer}" successfully updated'.format(primer = updated_primer))

                print("view")
               
                return index(request)

            else:
                # initial view for form with populated data from selected primer
                primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)

                primer = primer[0]

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
                context_dict["chrom_no_form"] = chrom_no_form
                context_dict["start_coordinate_37_form"] = start_coordinate_37_form
                context_dict["end_coordinate_37_form"] = end_coordinate_37_form
                context_dict["start_coordinate_38_form"] = start_coordinate_38_form
                context_dict["end_coordinate_38_form"] = end_coordinate_38_form
                context_dict["primer"] = primer
                print("else")

                return render(request, 'primer_db/edit_primer.html', context_dict)
                print("returned")

        # when delete button is pressed, delete current primer
        elif request.POST.get("delete_primer"):

            primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)
            del_primer = primer[0].primer_name
            primer[0].coordinates.delete()


            
            # delete message passed to index.html after deleting
            messages.success(request, 'Primer "{primer}" successfully deleted'.format(primer = del_primer))


            context_dict = {}
            table = PrimerDetailsTable(Models.PrimerDetails.objects.all())
            print("text3")
            # returns primer totals filtered by status
            total_archived = Models.PrimerDetails.objects.filter(status__status__icontains="archived").count()
            total_bank = Models.PrimerDetails.objects.filter(status__status__icontains="bank").count()
            total_order = Models.PrimerDetails.objects.filter(status__status__icontains="order").count()

            context_dict["table"] = table
            context_dict["total_archived"] = total_archived
            context_dict["total_bank"] = total_bank
            context_dict["total_order"] = total_order

            RequestConfig(request, paginate={'per_page': 50}).configure(table)

            return render(request, 'primer_db/index.html', context_dict)




    
    # initial view for form with populated data from selected primer
    print("initial primer edit view")

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
    chrom_no_form = Forms.ChromNoForm(initial = model_to_dict(coordinates))
    start_coordinate_37_form = Forms.StartCoordinate37Form(initial = model_to_dict(coordinates))
    end_coordinate_37_form = Forms.EndCoordinate37Form(initial = model_to_dict(coordinates))
    start_coordinate_38_form = Forms.StartCoordinate38Form(initial = model_to_dict(coordinates))
    end_coordinate_38_form = Forms.EndCoordinate38Form(initial = model_to_dict(coordinates))
    #location_form = Forms.LocationForm(initial = model_to_dict(primer))


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
    context_dict["chrom_no_form"] = chrom_no_form
    context_dict["start_coordinate_37_form"] = start_coordinate_37_form
    context_dict["end_coordinate_37_form"] = end_coordinate_37_form
    context_dict["start_coordinate_38_form"] = start_coordinate_38_form
    context_dict["end_coordinate_38_form"] = end_coordinate_38_form
    #context_dict["location_form"] = location_form

    context_dict["primer"] = primer


    return render(request, 'primer_db/edit_primer.html', context_dict)

