# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.template import loader
from django.views.generic.edit import FormView
from django.contrib import messages
from django.views.generic import  ListView
from .tables import PrimerDetailsTable
from django_tables2 import RequestConfig
from django.forms.models import model_to_dict
from django.shortcuts import get_object_or_404, redirect
from django.core.exceptions import ValidationError
import re

import primer_db.forms as Forms
import primer_db.models as Models


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
    if request.method == 'GET':

        var_pos = request.GET.get('var_pos', None)
        chrom_no = request.GET.get('chrom_no', None)
        
        context_dict["var_pos"] = var_pos
        context_dict["chrom_no"] = chrom_no


        primers37_id = []
        primers38_id = []


        if var_pos:
            
            var_pos = int(var_pos)

            chrom_list = Models.PrimerDetails.objects.filter(coordinates__chrom_no = chrom_no).values_list(
                'id', 'pairs__coverage_37', 'pairs__coverage_38', 'coordinates__chrom_no')


            for row in chrom_list:
                
                
                start_37 = int(re.search(r":(\d+)", row[1]).group().strip(":"))
                end_37 = int(re.search(r"\+(\d+)", row[1]).group().strip("+"))

                start_38 = int(re.search(r":(\d+)", row[2]).group().strip(":"))
                end_38 = int(re.search(r"\+(\d+)", row[2]).group().strip("+"))
               
                if start_37 < var_pos < end_37:
                    primers37_id.append(row[0])

                if start_38 < var_pos < end_38:
                    primers38_id.append(row[0])


            primers37 = Models.PrimerDetails.objects.filter(pk__in=primers37_id)
            primers38 = Models.PrimerDetails.objects.filter(pk__in=primers38_id)
            print(primers38)


            print(primers37)


            #context_dict["chrom_no"] = chrom_no
            context_dict["37_primers"] = primers37
            context_dict["38_primers"] = primers38

            table = PrimerDetailsTable(primers37, primers38)
            RequestConfig(request, paginate={'per_page': 50}).configure(table)

            context_dict["table"] = table

            return render(request, 'primer_db/index.html', context_dict)

    else:
        print("none")

    # function for filtering primers by part of primer name
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

    # function for filtering primers exact gene name
    if request.method == 'GET':

        gene_filter = request.GET.get('gene_filter', None)
        
        
        if gene_filter:
            gene_name = Models.PrimerDetails.objects.filter(gene = gene_filter)
            context_dict["gene_name"] = gene_name
            print(gene_name)

            table = PrimerDetailsTable(gene_name)
            RequestConfig(request, paginate={'per_page': 50}).configure(table)

            context_dict["table"] = table

            return render(request, 'primer_db/index.html', context_dict)

    else:

        pass
        print("searching passed")

    RequestConfig(request, paginate={'per_page': 30}).configure(table)

    return render(request, 'primer_db/index.html', context_dict)


# function for submitting new primers to database
def submit(request):
    template = loader.get_template('primer_db/submit.html')
   # return render(request, 'primer_db/index.html')

    context_dict = {}

    if request.method == "POST":
        
        name = request.POST.get('name')

        if name == "form1":
            print("form1")



        #if name == "form2":
         #   print("form2")

        # data is sent
        primer_form = Forms.PrimerForm(request.POST)
        sequence_form = Forms.SequenceForm(request.POST)
        status_form = Forms.StatusLocationForm(request.POST)
        arrival_date_form = Forms.ArrivalDateForm(request.POST)
        reference_form = Forms.ReferenceForm(request.POST)
        chrom_no_form = Forms.ChromNoForm(request.POST)
        submit_coordinate_form = Forms.SubmitCoordinateForm(request.POST)


        # check if data input to each form is valid
        if (primer_form.is_valid() and 
            sequence_form.is_valid() and
            status_form.is_valid() and
            arrival_date_form.is_valid() and
            reference_form.is_valid() and
            chrom_no_form.is_valid() and
            submit_coordinate_form.is_valid()
            ):


            # the form is valid
            primer_name = primer_form.cleaned_data["primer_name"]
            gene = primer_form.cleaned_data["gene"].upper() 
            sequence = sequence_form.cleaned_data["sequence"]
            status = status_form.cleaned_data["status"]
            gc_percent = primer_form.cleaned_data["gc_percent"]
            tm = primer_form.cleaned_data["tm"]
            #length = primer_form.cleaned_data["length"]
            comments = primer_form.cleaned_data["comments"]
            arrival_date = arrival_date_form.cleaned_data["arrival_date"]
            buffer = primer_form.cleaned_data["buffer"].capitalize()
            pcr_program = primer_form.cleaned_data["pcr_program"]
            forename = primer_form.cleaned_data["forename"].capitalize()
            surname = primer_form.cleaned_data["surname"].capitalize()
            reference = reference_form.cleaned_data["reference"]
            chrom_no = chrom_no_form.cleaned_data["chrom_no"]
            location = status_form.cleaned_data["location"]


            # checks if ref 37 or 38 has been selected and selects appropriate database field
            if reference == "37":

                start_coordinate_37 = submit_coordinate_form.cleaned_data["start_coordinate"]
                end_coordinate_37 = submit_coordinate_form.cleaned_data["end_coordinate"]
                start_coordinate_38 = None
                end_coordinate_38 = None

            elif reference == "38":   

                start_coordinate_38 = submit_coordinate_form.cleaned_data["start_coordinate"]
                end_coordinate_38 = submit_coordinate_form.cleaned_data["end_coordinate"]
                start_coordinate_37 = None
                end_coordinate_37 = None


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
                primer_name = primer_name, gene = gene, sequence = sequence, 
                gc_percent = gc_percent, tm = tm,
                comments =  comments, arrival_date = arrival_date,
                location = location,status = new_status, 
                scientist = new_scientist,pcr_program = new_pcr, 
                buffer = new_buffer, coordinates = new_coordinates)

            # success save message passed to submit.html
            messages.success(request, 'Primers successfully saved')
        

            # recreate the empty form
            primer_form = Forms.PrimerForm()
            sequence_form = Forms.SequenceForm()
            status_form = Forms.StatusLocationForm()
            arrival_date_form = Forms.ArrivalDateForm()
            reference_form = Forms.ReferenceForm()
            chrom_no_form = Forms.ChromNoForm()
            submit_coordinate_form = Forms.SubmitCoordinateForm()


            context_dict["primer_form"] = primer_form
            context_dict["sequence_form"] = sequence_form
            context_dict["status_form"] = status_form
            context_dict["arrival_date_form"] = arrival_date_form
            context_dict["reference_form"] = reference_form
            context_dict["chrom_no_form"] = chrom_no_form
            context_dict["submit_coordinate_form"] = submit_coordinate_form


            # return the submit page
            return render(request, 'primer_db/submit.html', context_dict)

    else:
            # if data is not sent, just display the form
        primer_form = Forms.PrimerForm()
        sequence_form = Forms.SequenceForm()
        status_form = Forms.StatusLocationForm()
        arrival_date_form = Forms.ArrivalDateForm()
        reference_form = Forms.ReferenceForm()
        chrom_no_form = Forms.ChromNoForm()
        submit_coordinate_form = Forms.SubmitCoordinateForm()

            
    context_dict["primer_form"] = primer_form
    context_dict["sequence_form"] = sequence_form
    context_dict["status_form"] = status_form
    context_dict["arrival_date_form"] = arrival_date_form
    context_dict["reference_form"] = reference_form
    context_dict["chrom_no_form"] = chrom_no_form
    context_dict["submit_coordinate_form"] = submit_coordinate_form

    return render(request, 'primer_db/submit.html', context_dict)


# function for edit_primer view of individual primers
def edit_primer(request, PrimerDetails_id):

    context_dict = {}

    if request.method == "POST":
        print("pressed")

        primer_form = Forms.PrimerForm(request.POST)
        sequence_form = Forms.SequenceForm(request.POST)
        status_form = Forms.StatusLocationForm(request.POST)
        arrival_date_form = Forms.ArrivalDateForm(request.POST)
        reference_form = Forms.ReferenceForm(request.POST)
        chrom_no_form = Forms.ChromNoForm(request.POST)
        coordinate_form = Forms.CoordinateForm(request.POST)


        # when update button is pressed, save updates made to current primer
        if request.POST.get("update_primer"):
            print("update button pressed")
            # checks the form is valid
            if (primer_form.is_valid() and 
                sequence_form.is_valid() and
                status_form.is_valid() and
                arrival_date_form.is_valid() and
                chrom_no_form.is_valid() and
                coordinate_form.is_valid() 
                ):
                print("update form is valid")

                # the form is valid
                primer_name = primer_form.cleaned_data["primer_name"]
                gene = primer_form.cleaned_data["gene"] 
                sequence = sequence_form.cleaned_data["sequence"]
                status = status_form.cleaned_data["status"]
                gcpercent = primer_form.cleaned_data["gc_percent"]
                tm = primer_form.cleaned_data["tm"]
                #length = primer_form.cleaned_data["length"]
                comments = primer_form.cleaned_data["comments"]
                arrival_date = primer_form.cleaned_data["arrival_date"]
                buffer = primer_form.cleaned_data["buffer"].capitalize()
                pcr_program = primer_form.cleaned_data["pcr_program"]
                forename = primer_form.cleaned_data["forename"].capitalize()
                surname = primer_form.cleaned_data["surname"].capitalize()
                chrom_no = chrom_no_form.cleaned_data["chrom_no"]
                start_coordinate_37 = coordinate_form.cleaned_data["start_coordinate_37"]
                end_coordinate_37 = coordinate_form.cleaned_data["end_coordinate_37"]
                start_coordinate_38 = coordinate_form.cleaned_data["start_coordinate_38"]
                end_coordinate_38 = coordinate_form.cleaned_data["end_coordinate_38"]
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
                    'gene' : gene, 'sequence': sequence, 
                    'gc_percent': gcpercent, 'tm': tm,
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
               
                #return render('primer_db/index.html', context_dict)
                return  redirect('/primer_db/')


            else:
                # view for form with populated data from selected primer if form is invalid
                primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)

                primer = primer[0]

                context_dict["primer_form"] = primer_form
                context_dict["sequence_form"] = sequence_form
                context_dict["status_form"] = status_form
                context_dict["arrival_date_form"] = arrival_date_form
                context_dict["chrom_no_form"] = chrom_no_form
                context_dict["coordinate_form"] = coordinate_form

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
    coordinates = primer.coordinates


    primer_details_dict = {

        'primer_name' : primer.primer_name,
        'gene' : primer.gene,
        'gc_percent' : primer.gc_percent,
        'tm' : primer.tm,
        #'length' : primer.length,
        'comments' : primer.comments,
        'buffer' : primer.buffer,
        'pcr_program' : primer.pcr_program,
        'forename' : primer.scientist.forename,
        'surname' : primer.scientist.surname
    }


    primer_form = Forms.PrimerForm(initial = primer_details_dict)
    sequence_form = Forms.SequenceForm(initial = model_to_dict(primer))
    status_form = Forms.StatusLocationForm(initial = model_to_dict(primer))
    arrival_date_form = Forms.ArrivalDateForm(initial = model_to_dict(primer))
    chrom_no_form = Forms.ChromNoForm(initial = model_to_dict(coordinates))
    coordinate_form = Forms.CoordinateForm(initial = model_to_dict(coordinates))


    context_dict["primer_form"] = primer_form
    context_dict["sequence_form"] = sequence_form
    context_dict["status_form"] = status_form
    context_dict["arrival_date_form"] = arrival_date_form
    context_dict["chrom_no_form"] = chrom_no_form
    context_dict["coordinate_form"] = coordinate_form
    context_dict["primer"] = primer


    return render(request, 'primer_db/edit_primer.html', context_dict)


# function for submitting pair of new primers to database
def submit_pair(request):
    template = loader.get_template('primer_db/submit_pair.html')
   # return render(request, 'primer_db/index.html')

    context_dict = {}

    if request.method == "POST":
        # data is sent
        primer_form1 = Forms.PrimerForm(request.POST, prefix ="primer_form1")
        sequence_form1 = Forms.SequenceForm(request.POST, prefix= "sequence_form1")
        status_form1 = Forms.StatusLocationForm(request.POST, prefix = "status_form1")
        arrival_date_form1 = Forms.ArrivalDateForm(request.POST, prefix = "arrival_date_form1")
        reference_form1 = Forms.ReferenceForm(request.POST, prefix = "reference_form1")
        chrom_no_form1 = Forms.ChromNoForm(request.POST, prefix = "chrom_no_form1")
        submit_coordinate_form1 = Forms.SubmitCoordinateForm(request.POST, prefix = "submit_coordinate_form1")

        primer_form2 = Forms.PrimerForm(request.POST, prefix="primer_form2")
        sequence_form2 = Forms.SequenceForm(request.POST, prefix = "sequence_form2")
        status_form2 = Forms.StatusLocationForm(request.POST, prefix = "status_form2")
        arrival_date_form2 = Forms.ArrivalDateForm(request.POST, prefix = "arrival_date_form2")
        reference_form2 = Forms.ReferenceForm(request.POST, prefix = "reference_form2")
        chrom_no_form2 = Forms.ChromNoForm(request.POST, prefix = "chrom_no_form2")
        submit_coordinate_form2 = Forms.SubmitCoordinateForm(request.POST, prefix = "submit_coordinate_form2")

        print(primer_form1, primer_form2)

        # check if data input to each form is valid
        if (primer_form1.is_valid() and 
            sequence_form1.is_valid() and
            status_form1.is_valid() and
            arrival_date_form1.is_valid() and
            reference_form1.is_valid() and
            chrom_no_form1.is_valid() and
            submit_coordinate_form1.is_valid() and

            primer_form2.is_valid() and 
            sequence_form2.is_valid() and
            status_form2.is_valid() and
            arrival_date_form2.is_valid() and
            reference_form2.is_valid() and
            chrom_no_form2.is_valid() and
            submit_coordinate_form2.is_valid()
            ):
            print("pair data valid")

            # the form is valid
            primer_name1 = primer_form1.cleaned_data["primer_name"]
            gene1 = primer_form1.cleaned_data["gene"].upper() 
            sequence1 = sequence_form1.cleaned_data["sequence"]
            status1 = status_form1.cleaned_data["status"]
            gc_percent1 = primer_form1.cleaned_data["gc_percent"]
            tm1 = primer_form1.cleaned_data["tm"]
            #length1 = primer_form1.cleaned_data["length"]
            comments1 = primer_form1.cleaned_data["comments"]
            arrival_date1 = arrival_date_form1.cleaned_data["arrival_date"]
            buffer1 = primer_form1.cleaned_data["buffer"].capitalize()
            pcr_program1 = primer_form1.cleaned_data["pcr_program"]
            forename1 = primer_form1.cleaned_data["forename"].capitalize()
            surname1 = primer_form1.cleaned_data["surname"].capitalize()
            reference1 = reference_form1.cleaned_data["reference"]
            chrom_no1 = chrom_no_form1.cleaned_data["chrom_no"]
            location1 = status_form1.cleaned_data["location"]

            primer_name2 = primer_form2.cleaned_data["primer_name"]
            gene2 = primer_form2.cleaned_data["gene"].upper() 
            sequence2 = sequence_form2.cleaned_data["sequence"]
            status2 = status_form2.cleaned_data["status"]
            gc_percent2 = primer_form2.cleaned_data["gc_percent"]
            tm2 = primer_form2.cleaned_data["tm"]
            #length2 = primer_form2.cleaned_data["length"]
            comments2 = primer_form2.cleaned_data["comments"]
            arrival_date2 = arrival_date_form2.cleaned_data["arrival_date"]
            buffer2 = primer_form2.cleaned_data["buffer"].capitalize()
            pcr_program2 = primer_form2.cleaned_data["pcr_program"]
            forename2 = primer_form2.cleaned_data["forename"].capitalize()
            surname2 = primer_form2.cleaned_data["surname"].capitalize()
            reference2 = reference_form2.cleaned_data["reference"]
            chrom_no2 = chrom_no_form2.cleaned_data["chrom_no"]
            location2 = status_form2.cleaned_data["location"]


            # checks if ref 37 or 38 has been selected and selects appropriate database field
            if reference1 == "37":

                start_coordinate_37_1 = submit_coordinate_form1.cleaned_data["start_coordinate"]
                end_coordinate_37_1 = submit_coordinate_form1.cleaned_data["end_coordinate"]
                start_coordinate_38_1 = None
                end_coordinate_38_1 = None

            elif reference1 == "38":   

                start_coordinate_38_1 = submit_coordinate_form2.cleaned_data["start_coordinate"]
                end_coordinate_38_1 = submit_coordinate_form2.cleaned_data["end_coordinate"]
                start_coordinate_37_1 = None
                end_coordinate_37_1 = None

            else:
                pass # needs something here although it can only be 37 or 38 since it is a choicefield


            # checks if ref 37 or 38 has been selected and selects appropriate database field
            if reference2 == "37":

                start_coordinate_37_2 = submit_coordinate_form2.cleaned_data["start_coordinate"]
                end_coordinate_37_2 = submit_coordinate_form2.cleaned_data["end_coordinate"]
                start_coordinate_38_2 = None
                end_coordinate_38_2 = None

            elif reference2 == "38":   

                start_coordinate_38_2 = submit_coordinate_form2.cleaned_data["start_coordinate"]
                end_coordinate_38_2 = submit_coordinate_form2.cleaned_data["end_coordinate"]
                start_coordinate_37_2 = None
                end_coordinate_37_2 = None

            else:
                pass # needs something here although it can only be 37 or 38 since it is a choicefield

            # save primer1 to database
            print("saving primer1")

            new_status1, created = Models.Status.objects.get_or_create(status = status1)

            new_scientist1, created = Models.Scientist.objects.get_or_create(
                forename = forename1, surname = surname1)

            new_pcr1, created = Models.PCRProgram.objects.get_or_create(
                pcr_program = pcr_program1)

            new_buffer1, created = Models.Buffer.objects.get_or_create(buffer = buffer1)

            new_coordinates1, created = Models.Coordinates.objects.get_or_create(
                start_coordinate_37 = start_coordinate_37_1, end_coordinate_37 = end_coordinate_37_1,
                start_coordinate_38 = start_coordinate_38_1, end_coordinate_38 = end_coordinate_38_1,
                reference = reference1, chrom_no = chrom_no1
                )

            print(primer_name1)

            new_primer1 =  Models.PrimerDetails.objects.create(
                primer_name = primer_name1, gene = gene1, sequence = sequence1, 
                gc_percent = gc_percent1, tm = tm1, 
                comments =  comments1, arrival_date = arrival_date1,
                location = location1,status = new_status1, 
                scientist = new_scientist1,pcr_program = new_pcr1, 
                buffer = new_buffer1, coordinates = new_coordinates1)
            print("saved primer1")


            # save primer 2 to database
            print("saving primer2")

            new_status2, created = Models.Status.objects.get_or_create(status = status2)

            new_scientist2, created = Models.Scientist.objects.get_or_create(
                forename = forename2, surname = surname2)

            new_pcr2, created = Models.PCRProgram.objects.get_or_create(
                pcr_program = pcr_program2)

            new_buffer2, created = Models.Buffer.objects.get_or_create(buffer = buffer2)

            new_coordinates2, created = Models.Coordinates.objects.get_or_create(
                start_coordinate_37 = start_coordinate_37_2, end_coordinate_37 = end_coordinate_37_2,
                start_coordinate_38 = start_coordinate_38_2, end_coordinate_38 = end_coordinate_38_2,
                reference = reference2, chrom_no = chrom_no2
                )

            new_primer2 =  Models.PrimerDetails.objects.create(
                primer_name = primer_name2, gene = gene2, sequence = sequence2, 
                gc_percent = gc_percent2, tm = tm2,
                comments =  comments2, arrival_date = arrival_date2,
                location = location2,status = new_status2, 
                scientist = new_scientist2,pcr_program = new_pcr2, 
                buffer = new_buffer2, coordinates = new_coordinates2)

            print("saved primer2")
            # success save message passed to submit.html
            messages.success(request, 'Primers successfully saved')
        

            # recreate the empty form
            primer_form1 = Forms.PrimerForm()
            sequence_form1 = Forms.SequenceForm()
            status_form1 = Forms.StatusLocationForm()
            arrival_date_form1 = Forms.ArrivalDateForm()
            reference_form1 = Forms.ReferenceForm()
            chrom_no_form1 = Forms.ChromNoForm()
            submit_coordinate_for1 = Forms.SubmitCoordinateForm()

            primer_form2 = Forms.PrimerForm()
            sequence_form2 = Forms.SequenceForm()
            status_form2 = Forms.StatusLocationForm()
            arrival_date_form2 = Forms.ArrivalDateForm()
            reference_form2 = Forms.ReferenceForm()
            chrom_no_form2 = Forms.ChromNoForm()
            submit_coordinate_form2 = Forms.SubmitCoordinateForm()


            context_dict["primer_form1"] = primer_form1
            context_dict["sequence_form1"] = sequence_form1
            context_dict["status_form1"] = status_form1
            context_dict["arrival_date_form1"] = arrival_date_form1
            context_dict["reference_form1"] = reference_form1
            context_dict["chrom_no_form1"] = chrom_no_form1
            context_dict["submit_coordinate_form1"] = submit_coordinate_form1

            context_dict["primer_form2"] = primer_form2
            context_dict["sequence_form2"] = sequence_form2
            context_dict["status_form2"] = status_form2
            context_dict["arrival_date_form2"] = arrival_date_form2
            context_dict["reference_form2"] = reference_form2
            context_dict["chrom_no_form2"] = chrom_no_form2
            context_dict["submit_coordinate_form2"] = submit_coordinate_form2


            # return the submit page
            return render(request, 'primer_db/submit_pair.html', context_dict)

    else:
            print("just displaying form, data not sent")
            # if data is not sent, just display the form
            primer_form1 = Forms.PrimerForm()
            sequence_form1 = Forms.SequenceForm()
            status_form1 = Forms.StatusLocationForm()
            arrival_date_form1 = Forms.ArrivalDateForm()
            reference_form1 = Forms.ReferenceForm()
            chrom_no_form1 = Forms.ChromNoForm()
            submit_coordinate_form1 = Forms.SubmitCoordinateForm()

            primer_form2 = Forms.PrimerForm()
            sequence_form2 = Forms.SequenceForm()
            status_form2 = Forms.StatusLocationForm()
            arrival_date_form2 = Forms.ArrivalDateForm()
            reference_form2 = Forms.ReferenceForm()
            chrom_no_form2 = Forms.ChromNoForm()
            submit_coordinate_form2 = Forms.SubmitCoordinateForm()

            
    context_dict["primer_form1"] = primer_form1
    context_dict["sequence_form1"] = sequence_form1
    context_dict["status_form1"] = status_form1
    context_dict["arrival_date_form1"] = arrival_date_form1
    context_dict["reference_form1"] = reference_form1
    context_dict["chrom_no_form1"] = chrom_no_form1
    context_dict["submit_coordinate_form1"] = submit_coordinate_form1

    context_dict["primer_form2"] = primer_form2
    context_dict["sequence_form2"] = sequence_form2
    context_dict["status_form2"] = status_form2
    context_dict["arrival_date_form2"] = arrival_date_form2
    context_dict["reference_form2"] = reference_form2
    context_dict["chrom_no_form2"] = chrom_no_form2
    context_dict["submit_coordinate_form2"] = submit_coordinate_form2

    return render(request, 'primer_db/submit_pair.html', context_dict)