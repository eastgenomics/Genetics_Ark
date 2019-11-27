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
from itertools import chain

import re
import subprocess
import sys

import primer_db.forms as Forms
import primer_db.models as Models

# path to ampping script
sys.path.insert(1, '/mnt/storage/home/rainfoj/Projects/primer_mapper/bin/') 
import primer_mapper_v2


def mapper1(primer_seq1, gene, ref):
    """
    Function for calling primer mapper when submitting single primer
    """
    res = primer_mapper_v2.main(primer_seq1, gene, ref)

    print("gene: ", gene)
    print(res)

    primer1_start = res[0]
    primer1_end = res[1]
    gene_chrom = res[2]

    return primer1_start, primer1_end, gene_chrom 


def mapper2(primer_seq1, gene, ref, primer_2):
    """
    Function for calling primer mapper when submitting pair of primers
    """
    primer_mapper.main(primer_seq1, gene, ref, primer_2)

    return coverage, primer1_start, primer1_end, primer2_start, primer2_end, gene_chrom


def gc_calculate(sequence):
    """
    Function for calculating GC % of submitted primer sequence
    """
    sequence = sequence.upper()
    gc_calc = round((((sequence.count('G') + sequence.count('C')) / len(sequence)) * 100), 2)

    return gc_calc


def tm_calculate(sequence):
    """
    Function for calculating Tm of submitted primer sequence
    """
    OLIGOTM = "/mnt/storage/apps/software/primer3_core/2.3.7/src/oligotm -sc 1 -tp 1 -n 0.6 -dv 1.5 "

    cmd = OLIGOTM + sequence
    tm_calc = subprocess.run(cmd, shell=True, stdout = subprocess.PIPE)
    tm_calc = tm_calc.stdout.decode("ascii").strip()

    return tm_calc


def index(request):

    """
    Homepage view of database; displays all primers inc. search functions and use of check boxes for changing
    status of multiple primers and recalculating coverage for a given pair of primers    

    """

    context_dict = {}
    filtered_dict = {}
    table = PrimerDetailsTable(Models.PrimerDetails.objects.all())

    # returns primer totals filtered by status for displaying on main db view
    total_archived = Models.PrimerDetails.objects.filter(status__status__icontains="archived").count()
    total_bank = Models.PrimerDetails.objects.filter(status__status__icontains="bank").count()
    total_order = Models.PrimerDetails.objects.filter(status__status__icontains="order").count()

    context_dict["table"] = table
    context_dict["total_archived"] = total_archived
    context_dict["total_bank"] = total_bank
    context_dict["total_order"] = total_order


    # function for filtering primers that have coverage for the given variant position  
    if request.method == 'GET':

        var_pos = request.GET.get('var_pos', None)
        chrom_no = request.GET.get('chrom_no', None)
        
        context_dict["var_pos"] = var_pos
        context_dict["chrom_no"] = chrom_no

        primers37_id = []
        primers38_id = []

        if var_pos:
            
            var_pos = int(var_pos)

            # get the id and coverage for all primers on given chromosome
            chrom_list = Models.PrimerDetails.objects.filter(coordinates__chrom_no = chrom_no).values_list(
                'id', 'pairs__coverage_37', 'pairs__coverage_38')


            for row in chrom_list:
                # loop through list of coverage and calculates if variant position is inside the coverage
            
                start_37 = int(re.search(r":(\d+)", row[1]).group().strip(":"))
                end_37 = int(re.search(r"\+(\d+)", row[1]).group().strip("+"))

                start_38 = int(re.search(r":(\d+)", row[2]).group().strip(":"))
                end_38 = int(re.search(r"\+(\d+)", row[2]).group().strip("+"))
               
                if start_37 <= var_pos <= end_37:
                    primers37_id.append(row[0])
                    print("37 match")

                if start_38 <= var_pos <= end_38:
                    primers38_id.append(row[0])
                    print("38 match")
                    print("primer id: ", primers38_id)


            # get query set for primer IDs that cover the variant position
            primers37 = Models.PrimerDetails.objects.filter(pk__in=primers37_id)
            primers38 = Models.PrimerDetails.objects.filter(pk__in=primers38_id)
            
            
            primers37_38 = list(chain(primers37, primers38)) # combine both querysets
            table = PrimerDetailsTable(primers37_38)

            RequestConfig(request, paginate={'per_page': 50}).configure(table)
            context_dict["table"] = table

            return render(request, 'primer_db/index.html', context_dict)

    else:
        print("none")



    # function for filtering primers on exact gene name
    if request.method == 'GET':

        gene_filter = request.GET.get('gene_filter', None)
        name_filter = request.GET.get('name_filter', None)

        
        if name_filter:
            primer_names = Models.PrimerDetails.objects.filter(primer_name__icontains=name_filter)
            context_dict["primer_names"] = primer_names
            table = PrimerDetailsTable(primer_names)

            filtered_dict["name"] = name_filter
            request.session['filtered_dict'] = filtered_dict

        
        if gene_filter:
            gene_name = Models.PrimerDetails.objects.filter(gene = gene_filter)
            context_dict["gene_name"] = gene_name
            table = PrimerDetailsTable(gene_name)

            filtered_dict["name"] = gene_filter
            request.session['filtered_dict'] = filtered_dict


        RequestConfig(request, paginate={'per_page': 50}).configure(table)
        context_dict["table"] = table

        return render(request, 'primer_db/index.html', context_dict)

    else:

        pass
        print("searching passed")



    # function for changing handling check boxes
    if request.method == 'POST':

        pks = request.POST.getlist('check')

        if 'recalc' in request.POST:
            # recalculating coverage from 2 selected primers

            print("recalculating")

            if len(pks) != 2:
                #need error message when 2 primers not selected and raise exception
                print("wrong no primers selected")
                messages.error(request, '{} primers selected, please select 2 primers'.format(len(pks)), extra_tags='error')


            gene1 = Models.PrimerDetails.objects.values_list('gene', flat=True).get(pk=pks[0])
            gene2 = Models.PrimerDetails.objects.values_list('gene', flat=True).get(pk=pks[1])

            if gene1 != gene2:
                # need error message when 2 selected primers aren't on same gene and raise exception
                pass


            primer1 = Models.PrimerDetails.objects.values_list('primer_name', flat=True).get(pk=pks[0]).split("_")[-1]
            primer2 = Models.PrimerDetails.objects.values_list('primer_name', flat=True).get(pk=pks[1]).split("_")[-1]
      
            print(primer1, primer2)

            if primer1[0] == "F" and primer2[0] == "R":
                print("Cool")

                f_start37 = Models.PrimerDetails.objects.values_list('coordinates__start_coordinate_37').get(pk=pks[0])[0]
                r_end37 = Models.PrimerDetails.objects.values_list('coordinates__end_coordinate_37').get(pk=pks[1])[0]
                f_start38 = Models.PrimerDetails.objects.values_list('coordinates__start_coordinate_38').get(pk=pks[0])[0]
                r_end38 = Models.PrimerDetails.objects.values_list('coordinates__end_coordinate_38').get(pk=pks[1])[0]
                
                print(f_start37, r_end37, f_start38, r_end38)
               
                pass

            elif primer1[0] == "R" and primer2[0] == "F":
                print("valid")

                f_start37 = Models.PrimerDetails.objects.values_list('coordinates__start_coordinate_37').get(pk=pks[1])[0]
                r_end37 = Models.PrimerDetails.objects.values_list('coordinates__end_coordinate_37').get(pk=pks[0])[0]
                f_start38 = Models.PrimerDetails.objects.values_list('coordinates__start_coordinate_38').get(pk=pks[1])[0]
                r_end38 = Models.PrimerDetails.objects.values_list('coordinates__end_coordinate_38').get(pk=pks[0])[0]

                print(f_start37, r_end37, f_start38, r_end38)

                pass

            else:
                # not a forward and reverse selected, need to raise exception and error message
                pass


            # need to calculate coverage from coordinates and display in a window


        elif 'new_status' in request.POST and 'recalc' not in request.POST:
            # changing status of multiple primers at once

            print("changing status")
            print(request.POST)

            new_status = request.POST.get('new_status') # get status to change to from POST data

            for pk in pks:

                update_status = Models.Status.objects.get_or_create(status=new_status)
                status_id = Models.Status.objects.filter(status__icontains=new_status).first().id
                Models.PrimerDetails.objects.filter(pk=pk).update(status=status_id)


            filtered_dict = request.session.get('filtered_dict', None)

            name = Models.PrimerDetails.objects.filter(gene = filtered_dict["name"])

            if len(name) == 0:
                # if filtered by primer name, length from gene name dict will be 0
                print("primer name filtered")
                name = Models.PrimerDetails.objects.filter(primer_name__icontains = filtered_dict["name"])
                print(name)


            table = PrimerDetailsTable(name)
            RequestConfig(request, paginate={'per_page': 50}).configure(table)

            context_dict["table"] = table

            return render(request, 'primer_db/index.html', context_dict)



    RequestConfig(request, paginate={'per_page': 50}).configure(table)


    return render(request, 'primer_db/index.html', context_dict)


def submit(request):

    """
    Function for submitting a single primer to the database
    """

    template = loader.get_template('primer_db/submit.html')

    context_dict = {}

    if request.method == "POST":

        print("submitting single primer")
        

        # data is sent
        primer_form = Forms.PrimerForm(request.POST)
        sequence_form = Forms.SequenceForm(request.POST)
        status_form = Forms.StatusLocationForm(request.POST)
        arrival_date_form = Forms.ArrivalDateForm(request.POST)


        # check if data input to each form is valid
        if (primer_form.is_valid() and 
            sequence_form.is_valid() and
            status_form.is_valid() and
            arrival_date_form.is_valid() 
            ):
            print("data valid")

            # the form is valid
            primer_name = primer_form.cleaned_data["primer_name"]
            gene = primer_form.cleaned_data["gene"].upper() 
            sequence = sequence_form.cleaned_data["sequence"]
            status = status_form.cleaned_data["status"]
            comments = primer_form.cleaned_data["comments"]
            arrival_date = arrival_date_form.cleaned_data["arrival_date"]
            buffer = primer_form.cleaned_data["buffer"].capitalize()
            pcr_program = primer_form.cleaned_data["pcr_program"]
            forename = primer_form.cleaned_data["forename"].capitalize()
            surname = primer_form.cleaned_data["surname"].capitalize()
            location = status_form.cleaned_data["location"]

            # call functions to calculate gc % and tm
            gc_percent = gc_calculate(sequence)
            tm = tm_calculate(sequence)


            # call primer_mapper to map primer to both 37 and 38, then return coords and chromosome number
            start_coordinate_37, end_coordinate_37, gene_chrom = mapper1(sequence, gene, 37)
            start_coordinate_38, end_coordinate_38, gene_chrom = mapper1(sequence, gene, 38)

            print("37 ", start_coordinate_37, end_coordinate_37)
            print("38 ", start_coordinate_38, end_coordinate_38)
            print("chrom no: ", gene_chrom)

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
                chrom_no = gene_chrom
                )

            new_primer =  Models.PrimerDetails.objects.create(
                primer_name = primer_name, gene = gene, sequence = sequence, 
                gc_percent = gc_percent, tm = tm,
                comments =  comments, arrival_date = arrival_date,
                location = location,status = new_status, 
                scientist = new_scientist,pcr_program = new_pcr, 
                buffer = new_buffer, coordinates = new_coordinates)

            # success save message passed to submit.html
            messages.success(request, 'Primer {} successfully saved with coordinates: GRCh37 {} - {} and GRCh38 {} - {}'.format(
                primer_name, start_coordinate_37, end_coordinate_37, start_coordinate_38, end_coordinate_38), extra_tags="success")
        
            return redirect('submit')

    else:
            # if data is not sent, just display the form
        primer_form = Forms.PrimerForm()
        sequence_form = Forms.SequenceForm()
        status_form = Forms.StatusLocationForm()
        arrival_date_form = Forms.ArrivalDateForm()

            
    context_dict["primer_form"] = primer_form
    context_dict["sequence_form"] = sequence_form
    context_dict["status_form"] = status_form
    context_dict["arrival_date_form"] = arrival_date_form


    return render(request, 'primer_db/submit.html', context_dict)


def submit_pair(request):

    """
    Function for submitting pair of new primers to database

    """

    template = loader.get_template('primer_db/submit_pair.html')


    context_dict = {}

    if request.method == "POST":
        # data is sent
        primer_form1 = Forms.PrimerForm(request.POST, prefix ="primer_form1")
        sequence_form1 = Forms.SequenceForm(request.POST, prefix= "sequence_form1")
        status_form1 = Forms.StatusLocationForm(request.POST, prefix = "status_form1")
        arrival_date_form1 = Forms.ArrivalDateForm(request.POST, prefix = "arrival_date_form1")
        
        primer_form2 = Forms.PrimerForm(request.POST, prefix="primer_form2")
        sequence_form2 = Forms.SequenceForm(request.POST, prefix = "sequence_form2")
        status_form2 = Forms.StatusLocationForm(request.POST, prefix = "status_form2")
        arrival_date_form2 = Forms.ArrivalDateForm(request.POST, prefix = "arrival_date_form2")


        # check if data input to each form is valid
        if (primer_form1.is_valid() and 
            sequence_form1.is_valid() and
            status_form1.is_valid() and
            arrival_date_form1.is_valid() and
            primer_form2.is_valid() and 
            sequence_form2.is_valid() and
            status_form2.is_valid() and
            arrival_date_form2.is_valid()
            ):
            print("pair data valid")


            # the form is valid
            primer_name1 = primer_form1.cleaned_data["primer_name"]
            gene1 = primer_form1.cleaned_data["gene"].upper() 
            sequence1 = sequence_form1.cleaned_data["sequence"]
            status1 = status_form1.cleaned_data["status"]
            comments1 = primer_form1.cleaned_data["comments"]
            arrival_date1 = arrival_date_form1.cleaned_data["arrival_date"]
            buffer1 = primer_form1.cleaned_data["buffer"].capitalize()
            pcr_program1 = primer_form1.cleaned_data["pcr_program"]
            forename1 = primer_form1.cleaned_data["forename"].capitalize()
            surname1 = primer_form1.cleaned_data["surname"].capitalize()
            location1 = status_form1.cleaned_data["location"]


            primer_name2 = primer_form2.cleaned_data["primer_name"]
            gene2 = primer_form2.cleaned_data["gene"].upper() 
            sequence2 = sequence_form2.cleaned_data["sequence"]
            status2 = status_form2.cleaned_data["status"]
            comments2 = primer_form2.cleaned_data["comments"]
            arrival_date2 = arrival_date_form2.cleaned_data["arrival_date"]
            buffer2 = primer_form2.cleaned_data["buffer"].capitalize()
            pcr_program2 = primer_form2.cleaned_data["pcr_program"]
            forename2 = primer_form2.cleaned_data["forename"].capitalize()
            surname2 = primer_form2.cleaned_data["surname"].capitalize()
            location2 = status_form2.cleaned_data["location"]



            # call functions to calculate gc % and tm
            gc_percent1 = gc_calculate(sequence1)
            tm1 = tm_calculate(sequence1)
            print("primer1 gc: ", gc_percent1)
            print("primer1 tm:: ", tm1)

            gc_percent2 = gc_calculate(sequence2)
            tm2 = tm_calculate(sequence2)
            print("primer2 gc: ", gc_percent2)
            print("primer2 tm:: ", tm2)


            # call primer_mapper to map primer to bnoth 37 and 38, then return coords and chromosome number
            coverage, start_coordinate_37, end_coordinate_37, gene_chrom = mapper2(sequence1, gene, 37, sequence2)

            
            start_coordinate_37, end_coordinate_37, gene_chrom = mapper2(sequence1, gene, 38, sequence2)

            print("37 ", start_coordinate_37, end_coordinate_37)
            print("38 ", start_coordinate_38, end_coordinate_38)
            print("chrom no: ", gene_chrom)



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
            messages.success(request, 'Primers successfully saved', extra_tags="success")
        

            # recreate the empty forms
            primer_form1 = Forms.PrimerForm()
            sequence_form1 = Forms.SequenceForm()
            status_form1 = Forms.StatusLocationForm()
            arrival_date_form1 = Forms.ArrivalDateForm()

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

            context_dict["primer_form2"] = primer_form2
            context_dict["sequence_form2"] = sequence_form2
            context_dict["status_form2"] = status_form2
            context_dict["arrival_date_form2"] = arrival_date_form2



            # return the submit page
            return render(request, 'primer_db/submit_pair.html', context_dict)

    else:
            print("just displaying form, data not sent")
            # if data is not sent, just display the form
            primer_form1 = Forms.PrimerForm()
            sequence_form1 = Forms.SequenceForm()
            status_form1 = Forms.StatusLocationForm()
            arrival_date_form1 = Forms.ArrivalDateForm()

            primer_form2 = Forms.PrimerForm()
            sequence_form2 = Forms.SequenceForm()
            status_form2 = Forms.StatusLocationForm()
            arrival_date_form2 = Forms.ArrivalDateForm()

            
    context_dict["primer_form1"] = primer_form1
    context_dict["sequence_form1"] = sequence_form1
    context_dict["status_form1"] = status_form1
    context_dict["arrival_date_form1"] = arrival_date_form1

    context_dict["primer_form2"] = primer_form2
    context_dict["sequence_form2"] = sequence_form2
    context_dict["status_form2"] = status_form2
    context_dict["arrival_date_form2"] = arrival_date_form2

    return render(request, 'primer_db/submit_pair.html', context_dict)


def edit_primer(request, PrimerDetails_id):
    """
    Function for edit view of a single primer when not in a primer pair
    """

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
        snp_form = Forms.SNPForm(request.POST)

        print(primer_form.is_bound)

        print("kuhkjhl", request.POST)
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
                comments = primer_form.cleaned_data["comments"]
                arrival_date = arrival_date_form.cleaned_data["arrival_date"]
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
                    # 'gc_percent': gcpercent, 'tm': tm,
                    'comments':  comments, 'arrival_date': arrival_date,
                    'location': location, 'status': new_status, 
                    'scientist': new_scientist,'pcr_program': new_pcr, 
                    'buffer': new_buffer, 'coordinates': new_coordinates})

                #messages.success(request, 'Primer successfully updated')


                primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)

                #new_primer = new_primer[0]
            
                updated_primer = primer[0].primer_name

                messages.success(request, 'Primer "{primer}" successfully updated'.format(primer = updated_primer),
                    extra_tags="success")

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
                context_dict["snp_form"] = snp_form

                return render(request, 'primer_db/edit_primer.html', context_dict)
                print("returned")


        # when delete button is pressed, delete current primer
        elif request.POST.get("delete_primer"):

            primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)
            del_primer = primer[0].primer_name
            primer[0].coordinates.delete()
            
            # delete message passed to index.html after deleting
            messages.success(request, 'Primer "{primer}" successfully deleted'.format(primer = del_primer),
                extra_tags="success")

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

            return  redirect('/primer_db/')

    
    # initial view for form with populated data from selected primer
    print("initial primer edit view")

    primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)
    primer = primer[0]
    coordinates = primer.coordinates
    status = primer.status

    print(primer)
    #print(model_to_dict(primer.pairs))

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
    location_form = Forms.StatusLocationForm(initial = model_to_dict(primer))
    arrival_date_form = Forms.ArrivalDateForm(initial = model_to_dict(primer))
    chrom_no_form = Forms.ChromNoForm(initial = model_to_dict(coordinates))
    coordinate_form = Forms.CoordinateForm(initial = model_to_dict(coordinates))
    status_form =  Forms.StatusLocationForm(initial = model_to_dict(status))
    snp_date_form = Forms.SNPForm(initial = model_to_dict(primer))
    snp_info_form = Forms.SNPForm(initial = model_to_dict(primer))

    print(model_to_dict(primer.status))
    print(" ")
    #print(chrom_no_form)

    context_dict["primer_form"] = primer_form
    context_dict["sequence_form"] = sequence_form
    context_dict["location_form"] = location_form
    context_dict["arrival_date_form"] = arrival_date_form
    context_dict["chrom_no_form"] = chrom_no_form
    context_dict["coordinate_form"] = coordinate_form
    context_dict["primer"] = primer
    context_dict["status_form"] = status_form
    context_dict["snp_date_form"] = snp_date_form
    context_dict["snp_info_form"] = snp_info_form

    return render(request, 'primer_db/edit_primer.html', context_dict)


def edit_pair(request, PrimerDetails_id):
    
    context_dict = {}

    """
    Function for edit view of a pair of primers
    """

    context_dict = {}

    if request.method == "POST":
        print("pressed")

        # data sent for first primer
        # primer_form1 = Forms.PrimerForm({'form1-primer_name':request.POST.getlist('primer_name')[0]}, prefix='form1')
        # sequence_form1 = Forms.SequenceForm({'form1-sequence':request.POST.getlist('sequence')[0]}, prefix ="form1")
        # status_form1 = Forms.StatusLocationForm({'form1-status':request.POST.getlist('status')[0]}, prefix ="form1")
        # arrival_date_form1 = Forms.ArrivalDateForm({'form1-arrival_date':request.POST.getlist('arrival_date')[0]}, prefix ="form1")
        # reference_form1 = Forms.ReferenceForm(request.POST, prefix ="reference_form1")
        # chrom_no_form1 = Forms.ChromNoForm({'form1-chrom_no':request.POST.getlist('chrom_no')[0]}, prefix ="form1")
        # coordinate_form1 = Forms.CoordinateForm({'form1-coordinate':request.POST.getlist('coordinate')[0]}, prefix ="form1")
        # snp_form1 = Forms.SNPForm({'form1-snp':request.POST.getlist('snp')[0]}, prefix ="form1")

        # data sent for second primer
        primer_form2 = Forms.PrimerForm(request.POST, prefix ="form2")
        sequence_form2 = Forms.SequenceForm(request.POST, prefix ="form2")
        status_form2 = Forms.StatusLocationForm(request.POST, prefix ="form2")
        arrival_date_form2 = Forms.ArrivalDateForm(request.POST, prefix ="form2")
        #reference_form1 = Forms.ReferenceForm(request.POST, prefix ="reference_form1")
        chrom_no_form2 = Forms.ChromNoForm(request.POST, prefix ="form2")
        coordinate_form2 = Forms.CoordinateForm(request.POST, prefix ="form2")
        snp_form2 = Forms.SNPForm(request.POST, prefix ="form2")

        # print(primer_form1)

        # when update button is pressed, save updates made to current primer
        if request.POST.get("update_primers"):
            print("update button pressed")

            # print(primer_form1.is_valid(), 
            #     sequence_form1.is_valid(),
            #     status_form1.is_valid(),
            #     arrival_date_form1.is_valid(),
            #     chrom_no_form1.is_valid(),
            #     coordinate_form1.is_valid(),
            #     snp_form1.is_valid())
                
            print(primer_form2.is_valid(), 
                sequence_form2.is_valid(),
                status_form2.is_valid(),
                arrival_date_form2.is_valid(),
                chrom_no_form2.is_valid(),
                coordinate_form2.is_valid(),
                snp_form2.is_valid())
            
            print(sequence_form1.errors.as_data())
            print(sequence_form1)

            return


            # checks the forms are valid
            if (primer_form1.is_valid() and 
                sequence_form1.is_valid() and
                status_form1.is_valid() and
                arrival_date_form1.is_valid() and
                chrom_no_form1.is_valid() and
                coordinate_form1.is_valid() and
                snp_form1.is_valid() and
                
                primer_form2.is_valid() and 
                sequence_form2.is_valid() and
                status_form2.is_valid() and
                arrival_date_form2.is_valid() and
                chrom_no_form2.is_valid() and
                coordinate_form2.is_valid() and
                snp_form2.is_valid()
                ):
        

                print("update form is valid")

                fields = ["primer_name", "gene", "sequence", "gc_percent", "tm", "buffer", "pcr_program", "arrival_date", "status", 
                "location", "snp_status", "snp_date", "snp_info", "comments", "forename", "surname", "chrom_no", 
                "start_coordinate_37", "end_coordinate_37", "start_coordinate_38", "end_coordinate_38", "location"]

                forms1 = []
                forms2 =[]

                # loop for adding correct fields to forms
                for i in fields:
                    if i == "sequence":
                        forms1.append(sequence_form1.cleaned_data[i])
                        forms2.append(sequence_form2.cleaned_data[i])
                    if i == "status":
                        forms1.append(status_form1.cleaned_data[i])
                        forms2.append(status_form2.cleaned_data[i])
                    if i == "location":
                        forms1.append(status_form1.cleaned_data[i])
                        forms2.append(status_form2.cleaned_data[i])
                    if i == "arrival_date":
                        forms1.append(arrival_date_form1.cleaned_data[i])
                        forms2.append(arrival_date_form2.cleaned_data[i])
                    if i == "chrom_no":
                        forms1.append(chrom_no_form1.cleaned_data[i])
                        forms2.append(chrom_no_form2.cleaned_data[i])
                    if "snp" in i:
                        forms1.append(snp_form1.cleaned_data[i])
                        forms2.append(snp_form2.cleaned_data[i])
                    if "coordinate" in i:
                        forms1.append(coordinate_form1.cleaned_data[i])
                        forms2.append(coordinate_form2.cleaned_data[i])
                    else:
                        forms1.append(primer_form1.cleaned_data[i])
                        forms2.append(primer_form2.cleaned_data[i])  

                # unpack variables for first form and save to db
                (primer_name, gene, sequence, gc_percent, tm, buffer, pcr_program, arrival_date, status, 
                location, snp_status, snp_date, snp_info, comments, forename, surname, chrom_no, 
                start_coordinate_37, end_coordinate_37, start_coordinate_38, end_coordinate_38, location) = forms1

                print("saving")
                new_status, created = Models.Status.objects.update_or_create(status = status)

                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                new_pcr, created = Models.PCRProgram.objects.update_or_create(pcr_program = pcr_program)

                new_buffer, created = Models.Buffer.objects.update_or_create(buffer = buffer)

                new_coordinates, created = Models.Coordinates.objects.update_or_create(
                    start_coordinate_37 = start_coordinate_37, end_coordinate_37 = end_coordinate_37,
                    start_coordinate_38 = start_coordinate_38, end_coordinate_38 = end_coordinate_38,
                    chrom_no = chrom_no
                    )

                new_primer =  Models.PrimerDetails.objects.update_or_create(
                    primer_name = primer_name, defaults={
                    'gene' : gene, 'sequence': sequence, 
                    # 'gc_percent': gcpercent, 'tm': tm,
                    'comments':  comments, 'arrival_date': arrival_date,'location': location, 
                    'status': new_status, 'scientist': new_scientist,'pcr_program': new_pcr, 
                    'buffer': new_buffer, 'coordinates': new_coordinates})


                # unpack variables for second form and save to db
                (primer_name, gene, sequence, gc_percent, tm, buffer, pcr_program, arrival_date, status, 
                location, snp_status, snp_date, snp_info, comments, forename, surname, chrom_no, 
                start_coordinate_37, end_coordinate_37, start_coordinate_38, end_coordinate_38, location) = forms2


                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                new_pcr, created = Models.PCRProgram.objects.update_or_create(pcr_program = pcr_program)

                new_buffer, created = Models.Buffer.objects.update_or_create(buffer = buffer)

                new_coordinates, created = Models.Coordinates.objects.update_or_create(
                    start_coordinate_37 = start_coordinate_37, end_coordinate_37 = end_coordinate_37,
                    start_coordinate_38 = start_coordinate_38, end_coordinate_38 = end_coordinate_38,
                    chrom_no = chrom_no
                    )

                new_primer =  Models.PrimerDetails.objects.update_or_create(
                    primer_name = primer_name, defaults={
                    'gene' : gene, 'sequence': sequence, 
                    # 'gc_percent': gcpercent, 'tm': tm,
                    'comments':  comments, 'arrival_date': arrival_date,'location': location, 
                    'status': new_status, 'scientist': new_scientist,'pcr_program': new_pcr, 
                    'buffer': new_buffer, 'coordinates': new_coordinates})

                # # the form is valid
                # primer_name = primer_form.cleaned_data["primer_name"]
                # gene = primer_form.cleaned_data["gene"] 
                # sequence = sequence_form.cleaned_data["sequence"]
                # status = status_form.cleaned_data["status"]
                # comments = primer_form.cleaned_data["comments"]
                # arrival_date = arrival_date_form.cleaned_data["arrival_date"]
                # buffer = primer_form.cleaned_data["buffer"].capitalize()
                # pcr_program = primer_form.cleaned_data["pcr_program"]
                # forename = primer_form.cleaned_data["forename"].capitalize()
                # surname = primer_form.cleaned_data["surname"].capitalize()
                # chrom_no = chrom_no_form.cleaned_data["chrom_no"]
                # start_coordinate_37 = coordinate_form.cleaned_data["start_coordinate_37"]
                # end_coordinate_37 = coordinate_form.cleaned_data["end_coordinate_37"]
                # start_coordinate_38 = coordinate_form.cleaned_data["start_coordinate_38"]
                # end_coordinate_38 = coordinate_form.cleaned_data["end_coordinate_38"]
                # location = status_form.cleaned_data["location"]


                # save primer to database
                # if primer is present updates, if not creates new instance in database

                print("saving")
                new_status, created = Models.Status.objects.update_or_create(status = status)

                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                new_pcr, created = Models.PCRProgram.objects.update_or_create(pcr_program = pcr_program)

                new_buffer, created = Models.Buffer.objects.update_or_create(buffer = buffer)

                new_coordinates, created = Models.Coordinates.objects.update_or_create(
                    start_coordinate_37 = start_coordinate_37, end_coordinate_37 = end_coordinate_37,
                    start_coordinate_38 = start_coordinate_38, end_coordinate_38 = end_coordinate_38,
                    chrom_no = chrom_no
                    )

                new_primer =  Models.PrimerDetails.objects.update_or_create(
                    primer_name = primer_name, defaults={
                    'gene' : gene, 'sequence': sequence, 
                    # 'gc_percent': gcpercent, 'tm': tm,
                    'comments':  comments, 'arrival_date': arrival_date,'location': location, 
                    'status': new_status, 'scientist': new_scientist,'pcr_program': new_pcr, 
                    'buffer': new_buffer, 'coordinates': new_coordinates})


                # for displaying success message
                primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)
                updated_primer = primer[0].primer_name

                messages.success(request, 'Primer "{primer}" successfully updated'.format(primer = updated_primer),
                    extra_tags="success")

                return  redirect('/primer_db/')


            else:
                # view for form with populated data from selected primer if form is invalid

                ### needs changing for 2 primers and add error messages

                print("form invalid")
                print(primer_form1.errors)

                primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)

                primer = primer[0]

                context_dict["primer_form"] = primer_form
                context_dict["sequence_form"] = sequence_form
                context_dict["status_form"] = status_form
                context_dict["arrival_date_form"] = arrival_date_form
                context_dict["chrom_no_form"] = chrom_no_form
                context_dict["coordinate_form"] = coordinate_form
                context_dict["snp_form"] = snp_form

                return render(request, 'primer_db/edit_primer.html', context_dict)
                print("returned")


        # when delete button is pressed, delete current primer
        elif request.POST.get("delete_primer"):

            primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)
            del_primer = primer[0].primer_name
            primer[0].coordinates.delete()
            
            # delete message passed to index.html after deleting
            messages.success(request, 'Primer "{primer}" successfully deleted'.format(primer = del_primer),
                extra_tags="success")

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

            return  redirect('/primer_db/')

        else:
            primer_name1 = Forms.PrimerForm(initial = primer1_details_dict, prefix = "form1")
            seqeunce1 = Forms.SequenceForm(initial = model_to_dict(primer1), prefix = "form1")
            status1 = Forms.StatusLocationForm(initial = model_to_dict(primer1), prefix = "form1")
            arrival1 = Forms.ArrivalDateForm(initial = model_to_dict(primer1), prefix = "form1")
            chrom1 = Forms.ChromNoForm(initial = model_to_dict(primer1.coordinates), prefix = "form1")
            coor1 = Forms.CoordinateForm(initial = model_to_dict(primer1.coordinates), prefix = "form1")
            status_loc1 = Forms.StatusLocationForm(initial = model_to_dict(primer1.status), prefix = "form1")
            snp1 = Forms.SNPForm(initial = model_to_dict(primer1), prefix = "form1")

            # data for second primer
            primer_name2 = Forms.PrimerForm(initial = primer2_details_dict, prefix = "form2")
            sequence2 = Forms.SequenceForm(initial = model_to_dict(primer2), prefix = "form2")
            status2 = Forms.StatusLocationForm(initial = model_to_dict(primer2), prefix = "form2")
            arrival2 = Forms.ArrivalDateForm(initial = model_to_dict(primer2), prefix = "form2")
            chrom2 = Forms.ChromNoForm(initial = model_to_dict(primer2.coordinates), prefix = "form2")
            coor2 = Forms.CoordinateForm(initial = model_to_dict(primer2.coordinates), prefix = "form2")
            status_loc2 = Forms.StatusLocationForm(initial = model_to_dict(primer2.status), prefix = "form2")
            snp2 = Forms.SNPForm(initial = model_to_dict(primer2), prefix = "form2")

    
    # ~~~~~~ initial view for form with populated data from selected primers ~~~~~~

    # check selected primer id
    primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)
    primer = primer[0]

    if primer.pairs_id:
        # if primer is from a pair and to be edited in pair form
        print("pair id present")
        primer1 = Models.PrimerDetails.objects.filter(pairs_id = primer.pairs_id)[0]
        primer2 = Models.PrimerDetails.objects.filter(pairs_id = primer.pairs_id)[1]
    else:
        # if primer has no associated pair, render single edit page with selected primer
        print("no pair id")
        return redirect('edit_primer', PrimerDetails_id = PrimerDetails_id)


    primer1_details_dict = {
       # dict for 1st primer details
        'primer_name' : primer1.primer_name, 'gene' : primer1.gene,
        'gc_percent' : primer1.gc_percent, 'tm' : primer1.tm,
        'comments' : primer1.comments, 'buffer' : primer1.buffer,
        'pcr_program' : primer1.pcr_program, 'forename' : primer1.scientist.forename,
        'surname' : primer1.scientist.surname
    }

    primer2_details_dict = {
        # dict for 2nd primer details
        'primer_name' : primer2.primer_name, 'gene' : primer2.gene,
        'gc_percent' : primer2.gc_percent, 'tm' : primer2.tm,
        'comments' : primer2.comments, 'buffer' : primer2.buffer,
        'pcr_program' : primer2.pcr_program, 'forename' : primer2.scientist.forename,
        'surname' : primer2.scientist.surname
    }

    # data for first primer
    context_dict["primer_form1"] = primer_name1
    context_dict["sequence_form1"] = sequence1
    context_dict["location_form1"] = status1
    context_dict["arrival_date_form1"] = arrival1
    context_dict["chrom_no_form1"] = chrom1
    context_dict["coordinate_form1"] = coor1
    context_dict["primer1"] = primer1 # 
    context_dict["status_form1"] = status1
    context_dict["snp_form1"] = snp1

    # data for second primer
    context_dict["primer_form2"] = primer_name2
    context_dict["sequence_form2"] = sequence2
    context_dict["location_form2"] = status_loc2
    context_dict["arrival_date_form2"] = arrival2
    context_dict["chrom_no_form2"] = chrom2
    context_dict["coordinate_form2"] = coor2
    context_dict["primer2"] = primer2 
    context_dict["status_form2"] = status2
    context_dict["snp_form2"] = snp2

    context_dict["coverage_form"] = Forms.CoverageForm(initial = model_to_dict(primer1.pairs))
    

    return render(request, 'primer_db/edit_pair.html', context_dict)