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
from django.utils import timezone
from itertools import chain

import re
import subprocess
import sys
import datetime
import os
import logging

import primer_db.forms as Forms
import primer_db.models as Models

# path to mapping script
sys.path.insert(1, '/mnt/storage/home/rainfoj/Projects/primer_mapper/bin/') 
import primer_mapper_v2

sys.path.insert(1, '/mnt/storage/home/kimy/projects/gnomAD_queries/') 
import gnomAD_queries

logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'file': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'file',
            'filename': 'primer_db/logs/views.log',
            'mode': 'a',
            'maxBytes': 10000000,
            'backupCount': 5,
        }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['file']
        }
    }
})

logger = logging.getLogger(__name__)

def mapper1(seq, gene, ref):
    """
    Function for calling primer mapper when submitting single primer
    """
    mapping_result = primer_mapper_v2.main(seq, gene, ref)

    primer_start, primer_end, gene_chrom, strand = mapping_result

    return primer_start, primer_end, gene_chrom, strand


def mapper2(primer_seq1, gene, ref, primer_seq2):
    """
    Function for calling primer mapper when submitting pair of primers
    """
    (coverage, primer1_start, primer1_end,
     primer2_start, primer2_end, gene_chrom, primer1_strand, primer2_strand) = primer_mapper_v2.main(primer_seq1, gene, ref, primer_seq2)

    return coverage, primer1_start, primer1_end, primer2_start, primer2_end, gene_chrom, primer1_strand, primer2_strand


def multiple_mapping(new_primer1, new_primer2, sequence1, sequence2, gene_chrom):
    """
    Function to run SMALT to check for multiple mapping 
    """

    print("checking for multiple mapping")

    primers_file = "primers.fasta"

    with open(primers_file, 'w+') as primer_fasta:
        # add forward and reverse sequences to temp. file for running smalt
        print("opening file")

        primer_fasta.write(">{}\n{}\n".format("f", sequence1.strip()))
        primer_fasta.write(">{}\n{}\n".format("r", sequence2.strip()))

        primer_fasta.close()

    ref_37 = "/mnt/storage/data/refs/homo_sapiens/GRCh37/Homo_sapiens_assembly37"
    ref_38 = "/mnt/storage/data/refs/homo_sapiens/GRCh38/Homo_sapiens_assembly38"

    cmd_37 = "smalt map -d -1 -m 15 {} {}".format(ref_37, primers_file)
    cmd_38 = "smalt map -d -1 -m 15 {} {}".format(ref_38, primers_file)		

    # try mapping on GRCh37
    smalt_out_37 = subprocess.run(cmd_37, shell = True, stdout = subprocess.PIPE).stdout.decode("ascii").strip()
    smalt_out_37 = [line for line in smalt_out_37.split("\n") if not line.startswith("@")]

    match_list = []
    match_list2 = []

    for line in smalt_out_37:
        line = line.split('\t')

        if gene_chrom == line[2]:
            # get just primers on correct chromosome

            match = int(len(line[9]) - int(line[12].split(':')[2]))

            if match <= 5:
                match_list.append(match)
        

    if len(match_list) <= 2:
        # no multiple mappings on GRCh37, trying GRCh38

        smalt_out_38 = subprocess.run(cmd_38, shell = True, stdout = subprocess.PIPE).stdout.decode("ascii").strip()
        smalt_out_38 = [line for line in smalt_out_38.split("\n") if not line.startswith("@")]

        for line in smalt_out_38:
            line = line.split('\t')
            match = 0

            if gene_chrom == line[2]:
                # get just primers on correct chromosome
                match = int(len(line[9]) - int(line[12].split(':')[2]))
            
                if match <= 5:
                    match_list2.append(match)
        
    if len(match_list) > 2 or len(match_list2) > 2:
        
        # multiple mapping detected, adding new comment
        comment = "Multiple mapping detected, check before use"

        if new_primer1.comments or new_primer2.comments:
            # comments already exist, add to them
                new_primer1_comments = new_primer1.comments + "\nMultiple mapping detected, check before use"
                new_primer2_comments = new_primer2.comments + "\nMultiple mapping detected, check before use"

                Models.PrimerDetails.objects.update_or_create(
                    name = new_primer1.name, defaults={'comments' : new_primer1_comments})
                Models.PrimerDetails.objects.update_or_create(
                    name = new_primer2.name, defaults={'comments' : new_primer2_comments})

        
        else:
            # just add comment
            Models.PrimerDetails.objects.update_or_create(
                name = new_primer1.name, defaults={'comments' : comment})
            Models.PrimerDetails.objects.update_or_create(
                name = new_primer2.name, defaults={'comments' : comment})

        
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


def snp_check(
    gene, primer_start_37, primer_end_37,
    primer_start_38, primer_end_38
):
    """
    Function to run SNP check script
    """

    snp_date = datetime.datetime.now().strftime("%Y-%m-%d")
    snp_info = []

    for ref in ["37", "38"]:
        snp_pos = []
        snp_detail = []

        total_snps = gnomAD_queries.snp_check_query(gene, ref)

        if total_snps:
            for snp in total_snps:
                if ref == "37":
                    if primer_start_37 <= snp['pos'] <= primer_end_37:
                        snp_pos.append(snp['pos'] - primer_start_37)
                        snp_detail.append("{}?dataset=gnomad_r2_1".format(snp['variant_id']))
                elif ref == "38":
                    if primer_start_38 <= snp['pos'] <= primer_end_38:
                        snp_pos.append(snp['pos'] - primer_start_38)
                        snp_detail.append("{}?dataset=gnomad_r3".format(snp['variant_id']))

    if snp_detail:
        for i, snp in enumerate(snp_detail):
            snp_info.append("+{}, {}".format(
                snp_pos[i], snp))

        snp_status = 2
    else:
        snp_status = 1

    return snp_status, snp_date, snp_info


def index(request):

    """
    Homepage view of database; displays all primers inc. search functions and use of check boxes for changing
    status of multiple primers and recalculating coverage for a given pair of primers    

    """

    context_dict = {}
    filtered_dict = {}
    filtering = False



    # function for filtering primers that have coverage for the given variant position  
    if request.method == 'GET':
        var_pos = request.GET.get('var_pos', None)
        chrom_no = request.GET.get('chrom_no', None)
        gene_filter = request.GET.get('gene_filter', None)
        name_filter = request.GET.get('name_filter', None)
        
        context_dict["var_pos"] = var_pos
        context_dict["chrom_no"] = chrom_no

        filter_grch37 = Models.PrimerDetails.objects.none()
        filter_grch38 = Models.PrimerDetails.objects.none()
        filter_name = Models.PrimerDetails.objects.none()
        filter_gene = Models.PrimerDetails.objects.none()

        if var_pos:
            filtering = True
            primers37 = []
            primers38 = []

            var_pos = int(var_pos)

            # get the id and coverage for all primers on given chromosome
            position_filtered_primers = Models.PrimerDetails.objects.filter(coordinates__chrom_no = chrom_no)
            
            for primer in position_filtered_primers:
                coordinates = primer.coordinates

                if coordinates.start_coordinate_37 <= var_pos <= coordinates.end_coordinate_37:
                    primers37.append(primer.id)

                if coordinates.start_coordinate_38 <= var_pos <= coordinates.end_coordinate_38:
                    primers38.append(primer.id)

            # get query set for primer IDs that cover the variant position
            filter_grch37 = Models.PrimerDetails.objects.filter(pk__in=primers37)
            filter_grch38 = Models.PrimerDetails.objects.filter(pk__in=primers38)

        if name_filter:
            filtering = True
            filter_name = Models.PrimerDetails.objects.filter(name__icontains=name_filter)

            filtered_dict["name"] = name_filter
            request.session['filtered_dict'] = filtered_dict

        if gene_filter:
            filtering = True
            filter_gene = Models.PrimerDetails.objects.filter(gene = gene_filter)

            filtered_dict["name"] = gene_filter
            request.session['filtered_dict'] = filtered_dict

        if filtering:
            # table filtered by something
            filtered_primers = list(chain(filter_grch37, filter_grch38, filter_name, filter_gene)) # combine both querysets
            table = PrimerDetailsTable(filtered_primers)
        else:
            # original table not filtered
            table = PrimerDetailsTable(Models.PrimerDetails.objects.all())
            if request.session.get("filtered_dict", None):
                del request.session["filtered_dict"]

    # function for changing handling check boxes
    elif request.method == 'POST':

        pks = request.POST.getlist('check')

        if 'recalc' in request.POST:
            print("recalculating")

            amplicon_length_37 = None
            amplicon_length_38 = None
            popup_msg = []

            if len(pks) != 2:
                messages.error(request, '{} primers selected, please select 2 primers'.format(len(pks)), extra_tags='error')

            gene1 = Models.PrimerDetails.objects.values_list('gene', flat=True).get(pk=pks[0])
            gene2 = Models.PrimerDetails.objects.values_list('gene', flat=True).get(pk=pks[1])

            if gene1 != gene2:
                msg = "2 different genes ({}, {}) for the primer coverage calculation".format(gene1, gene2)
                messages.error(request, msg, extra_tags='error')

            elif primer2.coordinates.strand == "+" and primer1.coordinates.strand == "-":
                f_start37 = primer2.coordinates.start_coordinate_37
                r_end37 = primer1.coordinates.end_coordinate_37
                f_start38 = primer2.coordinates.start_coordinate_38
                r_end38 = primer1.coordinates.end_coordinate_38

            if primer1[0] == "F" and primer2[0] == "R":
                f_start37 = Models.PrimerDetails.objects.values_list('coordinates__start_coordinate_37').get(pk=pks[0])[0]
                r_end37 = Models.PrimerDetails.objects.values_list('coordinates__end_coordinate_37').get(pk=pks[1])[0]
                f_start38 = Models.PrimerDetails.objects.values_list('coordinates__start_coordinate_38').get(pk=pks[0])[0]
                r_end38 = Models.PrimerDetails.objects.values_list('coordinates__end_coordinate_38').get(pk=pks[1])[0]

            elif primer1[0] == "R" and primer2[0] == "F":
                f_start37 = Models.PrimerDetails.objects.values_list('coordinates__start_coordinate_37').get(pk=pks[1])[0]
                r_end37 = Models.PrimerDetails.objects.values_list('coordinates__end_coordinate_37').get(pk=pks[0])[0]
                f_start38 = Models.PrimerDetails.objects.values_list('coordinates__start_coordinate_38').get(pk=pks[1])[0]
                r_end38 = Models.PrimerDetails.objects.values_list('coordinates__end_coordinate_38').get(pk=pks[0])[0]

            else:
                msg = "You need a forward and a reverse primer"
                messages.error(request, msg, extra_tags='error')

            # need to calculate coverage from coordinates and display in a window


        elif 'new_status' in request.POST and 'recalc' not in request.POST:
            new_status = request.POST.get('new_status') # get status to change to from POST data

            for pk in pks:
                update_status = Models.Status.objects.get_or_create(name=new_status)
                status_id = Models.Status.objects.filter(name__icontains=new_status).first().id
                Models.PrimerDetails.objects.filter(pk=pk).update(status=status_id)

            filtered_dict = request.session.get('filtered_dict', None)

            if filtered_dict:
                name = Models.PrimerDetails.objects.filter(gene = filtered_dict["name"])

                if len(name) == 0:
                    # if filtered by primer name, length from gene name dict will be 0
                    print("primer name filtered")
                    name = Models.PrimerDetails.objects.filter(name__icontains = filtered_dict["name"])
                    print(name)

                table = PrimerDetailsTable(name)

            else:
                table = PrimerDetailsTable(Models.PrimerDetails.objects.all())
                if request.session.get("filtered_dict", None):
                    del request.session["filtered_dict"]

    # returns primer totals filtered by status for displaying on main db view
    total_archived = Models.PrimerDetails.objects.filter(status__name__icontains="archived").count()
    total_bank = Models.PrimerDetails.objects.filter(status__name__icontains="bank").count()
    total_order = Models.PrimerDetails.objects.filter(status__name__icontains="order").count()

    context_dict["table"] = table
    context_dict["total_archived"] = total_archived
    context_dict["total_bank"] = total_bank
    context_dict["total_order"] = total_order

    RequestConfig(request, paginate={'per_page': 50}).configure(table)

    return render(request, 'primer_db/index.html', context_dict)


def submit(request):

    """
    Function for submitting a single primer to the database
    """

    template = loader.get_template('primer_db/submit.html')

    context_dict = {}

    if request.method == "POST":
        # data is sent
        primer_form = Forms.PrimerForm(request.POST)
        sequence_form = Forms.SequenceForm(request.POST)
        status_form = Forms.StatusLocationForm(request.POST)
        arrival_date_form = Forms.ArrivalDateForm(request.POST)

        list_forms = [primer_form, sequence_form, status_form, arrival_date_form]

        context_dict["primer_form"] = Forms.PrimerForm()
        context_dict["sequence_form"] = Forms.SequenceForm()
        context_dict["status_form"] = Forms.StatusLocationForm()
        context_dict["arrival_date_form"] = Forms.ArrivalDateForm()

        logger.info("Submitting primer")
        logger.info("Data submitted by scientist:")

        for field, value in request.POST.items():
            if field != "csrfmiddlewaretoken" or "button" not in field:
                logger.info(" - {}: {}".format(field, value))


        # check if data input to each form is valid
        if (primer_form.is_valid() and 
            sequence_form.is_valid() and
            status_form.is_valid() and
            arrival_date_form.is_valid() 
        ):
            # the form is valid
            name = primer_form.cleaned_data["name"]
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
            start_coordinate_37, end_coordinate_37, gene_chrom, strand = mapper1(sequence, gene, 37)
            start_coordinate_38, end_coordinate_38, gene_chrom, strand = mapper1(sequence, gene, 38)

            if all((start_coordinate_37, end_coordinate_37, start_coordinate_38, end_coordinate_38)):
                # call function to check for SNPs
                snp_status, snp_date, snp_info = snp_check(
                    gene, start_coordinate_37, end_coordinate_37,
                    start_coordinate_38, end_coordinate_38
                )

                if snp_info:
                    logger.info("Detected snps in primer")
                else:
                    logger.info("No snps detected")

                # save primer to database
                status_object = Models.Status.objects.filter(name = status)[0]

                logger.info("Using status: {}".format(status_object))

                new_scientist, created = Models.Scientist.objects.get_or_create(
                    forename = forename, surname = surname)

                if created:
                    logger.info("New scientist added to db: {}".format(new_scientist))
                else:
                    logger.info("Scientist submitting primer: {}".format(new_scientist))

                new_pcr, created = Models.PCRProgram.objects.get_or_create(
                    name = pcr_program)

                if created:
                    logger.info("New pcr program added to db: {}".format(new_pcr))
                else:
                    logger.info("Using pcr program: {}".format(new_pcr))

                new_buffer, created = Models.Buffer.objects.get_or_create(name = buffer)

                if created:
                    logger.info("New buffer added to db: {}".format(new_buffer))
                else:
                    logger.info("Using buffer: {}".format(new_buffer))

                new_coordinates, created = Models.Coordinates.objects.get_or_create(
                    start_coordinate_37 = start_coordinate_37, end_coordinate_37 = end_coordinate_37,
                    start_coordinate_38 = start_coordinate_38, end_coordinate_38 = end_coordinate_38, 
                    chrom_no = gene_chrom, strand = strand
                    )

                if created:
                    logger.info("New coordinates added to db: {}".format(new_coordinates))
                else:
                    logger.info("Using coordinates: {}".format(new_coordinates))

                new_primer = Models.PrimerDetails.objects.create(
                    name = name, gene = gene, sequence = sequence, 
                    gc_percent = gc_percent, tm = tm,
                    comments =  comments, arrival_date = arrival_date,
                    location = location, snp_status = snp_status,
                    snp_date = snp_date, snp_info = ";".join(snp_info),
                    status = status_object, scientist = new_scientist, 
                    pcr_program = new_pcr, buffer = new_buffer, 
                    coordinates = new_coordinates)

                logger.info("Created primer: {} {}".format(new_primer.id, new_primer))
                logger.info(" - Primer gene: {}".format(new_primer.gene))
                logger.info(" - Primer sequence: {}".format(new_primer.sequence))
                logger.info(" - Primer gc %: {}".format(new_primer.gc_percent))
                logger.info(" - Primer tm: {}".format(new_primer.tm))

                # success save message passed to submit.html
                messages.success(request, 'Primer {} successfully saved with coordinates: GRCh37 {} - {} and GRCh38 {} - {}'.format(
                    name, start_coordinate_37, end_coordinate_37, start_coordinate_38, end_coordinate_38), extra_tags="alert-success")

                #return redirect('submit')
                return render(request, 'primer_db/submit.html', context_dict)

            else:
                messages.error(request, "The sequence provided didn't map to gene provided", extra_tags="alert-danger")
                logger.error("Sequence didn't map")

        else:
            for form in list_forms:
                if not form.is_valid():
                    error = form.errors["__all__"]
                    messages.add_message(
                        request,
                        messages.ERROR,
                        error,
                        extra_tags='alert-danger'
                    )

            return render(request, 'primer_db/submit.html', context_dict)

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
        # trick to fool form2
        data = request.POST.copy()
        print(data)
        data["form2-gene"] = data["form1-gene"]
        data["form2-forename"] = data["form1-forename"]
        data["form2-surname"] = data["form1-surname"]
        data["form2-pcr_program"] = data["form1-pcr_program"]
        data["form2-buffer"] = data["form1-buffer"]

        # data is sent
        primer_form1 = Forms.PrimerForm(request.POST, prefix = "form1")
        sequence_form1 = Forms.SequenceForm(request.POST, prefix = "form1")
        status_form1 = Forms.StatusLocationForm(request.POST, prefix = "form1")
        arrival_date_form1 = Forms.ArrivalDateForm(request.POST, prefix = "form1")
        
        primer_form2 = Forms.PrimerForm(data, prefix = "form2")
        sequence_form2 = Forms.SequenceForm(request.POST, prefix = "form2")
        status_form2 = Forms.StatusLocationForm(request.POST, prefix = "form2")
        arrival_date_form2 = Forms.ArrivalDateForm(request.POST, prefix = "form2")

        logger.info("Submitting primer")
        logger.info("Data submitted by scientist:")

        for field, value in request.POST.items():
            if field != "csrfmiddlewaretoken" or "button" not in field:
                logger.info(" - {}: {}".format(field, value))

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
            # the form is valid
            primer_name1 = primer_form1.cleaned_data["name"]
            gene = primer_form1.cleaned_data["gene"].upper() 
            sequence1 = sequence_form1.cleaned_data["sequence"].strip()
            status1 = status_form1.cleaned_data["status"]
            comments1 = primer_form1.cleaned_data["comments"]
            arrival_date1 = arrival_date_form1.cleaned_data["arrival_date"]
            buffer = primer_form1.cleaned_data["buffer"].capitalize()
            pcr_program = primer_form1.cleaned_data["pcr_program"]
            forename = primer_form1.cleaned_data["forename"].capitalize()
            surname = primer_form1.cleaned_data["surname"].capitalize()
            location1 = status_form1.cleaned_data["location"]

            primer_name2 = primer_form2.cleaned_data["name"]
            sequence2 = sequence_form2.cleaned_data["sequence"].strip()
            status2 = status_form2.cleaned_data["status"]
            comments2 = primer_form2.cleaned_data["comments"]
            arrival_date2 = arrival_date_form2.cleaned_data["arrival_date"]
            location2 = status_form2.cleaned_data["location"]

            if primer_name1 != primer_name2:
                # call functions to calculate gc % and tm
                gc_percent1 = gc_calculate(sequence1)
                tm1 = tm_calculate(sequence1)

                gc_percent2 = gc_calculate(sequence2)
                tm2 = tm_calculate(sequence2)

                # call primer_mapper to map primer to both 37 and 38, then return coords and chromosome number
                (coverage_37, primer1_start_37, primer1_end_37,
                 primer2_start_37, primer2_end_37, gene_chrom,
                 primer1_strand, primer2_strand) = mapper2(sequence1, gene, 37, sequence2)

                (coverage_38, primer1_start_38, primer1_end_38,
                 primer2_start_38, primer2_end_38, gene_chrom,
                 primer1_strand, primer2_strand) = mapper2(sequence1, gene, 38, sequence2)

                if all((primer1_start_37, primer1_end_37, primer2_start_37, primer2_start_37,
                        primer1_start_38, primer1_end_38, primer2_start_38, primer2_end_38)
                ):
                    logger.info("Common info for primers:")

                    new_pair = Models.Pairs.objects.create(
                        coverage_37 = coverage_37, coverage_38 = coverage_38
                    )

                    logger.info("Pair created, id: {}".format(new_pair.id))

                    new_scientist, created = Models.Scientist.objects.get_or_create(
                        forename = forename, surname = surname)

                    if created:
                        logger.info("New scientist added to db: {}".format(new_scientist))
                    else:
                        logger.info("Scientist submitting primer: {}".format(new_scientist))

                    new_pcr, created = Models.PCRProgram.objects.get_or_create(
                        name = pcr_program)

                    if created:
                        logger.info("New pcr program added to db: {}".format(new_pcr))
                    else:
                        logger.info("Using pcr program: {}".format(new_pcr))

                    new_buffer, created = Models.Buffer.objects.get_or_create(name = buffer)

                    if created:
                        logger.info("New buffer added to db: {}".format(new_buffer))
                    else:
                        logger.info("Using buffer: {}".format(new_buffer))

                    #############################################################

                    logger.info("Data for primer1:")

                    snp_status1, snp_date1, snp_info1 = snp_check(
                        gene, primer1_start_37, primer1_end_37,
                        primer1_start_38, primer1_end_38
                    )

                    if snp_info1:
                        logger.info("SNPs detected in primer")
                    else:
                        logger.info("No SNPs detected in primer")

                    new_status1 = Models.Status.objects.filter(name = status1)[0]

                    logger.info("Status of primer: {}".format(new_status1))

                    new_coordinates1, created = Models.Coordinates.objects.get_or_create(
                        start_coordinate_37 = primer1_start_37, end_coordinate_37 = primer1_end_37,
                        start_coordinate_38 = primer1_start_38, end_coordinate_38 = primer1_end_38,
                        chrom_no = gene_chrom, strand = primer1_strand
                        )

                    if created:
                        logger.info("New coordinates added to db: {}".format(new_coordinates1))
                    else:
                        logger.info("Using coordinates: {}".format(new_coordinates1))

                    new_primer1, created =  Models.PrimerDetails.objects.update_or_create(
                        name = primer_name1, gene = gene, sequence = sequence1, 
                        gc_percent = gc_percent1, tm = tm1, pairs = new_pair,
                        comments =  comments1, arrival_date = arrival_date1,
                        location = location1, status = new_status1, 
                        scientist = new_scientist, pcr_program = new_pcr, 
                        buffer = new_buffer, coordinates = new_coordinates1,
                        snp_status = snp_status1, snp_info = ";".join(snp_info1), snp_date = snp_date1
                    )
                    
                    logger.info("Created primer: {} {}".format(new_primer1.id, new_primer1))
                    logger.info(" - Primer gene: {}".format(new_primer1.gene))
                    logger.info(" - Primer sequence: {}".format(new_primer1.sequence))
                    logger.info(" - Primer gc %: {}".format(new_primer1.gc_percent))
                    logger.info(" - Primer tm: {}".format(new_primer1.tm))

                    #############################################################

                    logger.info("Data for primer2")

                    snp_status2, snp_date2, snp_info2 = snp_check(
                        gene, primer2_start_37, primer2_end_37,
                        primer2_start_38, primer2_end_38
                    )

                    if snp_info2:
                        logger.info("SNPs detected in primer")
                    else:
                        logger.info("No SNPs detected in primer")

                    # save primer 2 to database
                    new_status2, created = Models.Status.objects.get_or_create(name = status2)

                    logger.info("Status of primer2: {}".format(new_status2))

                    new_coordinates2, created = Models.Coordinates.objects.get_or_create(
                        start_coordinate_37 = primer2_start_37, end_coordinate_37 = primer2_end_37,
                        start_coordinate_38 = primer2_start_38, end_coordinate_38 = primer2_end_38,
                        chrom_no = gene_chrom, strand = primer2_strand
                        )

                    if created:
                        logger.info("New coordinates added to db: {}".format(new_coordinates2))
                    else:
                        logger.info("Using coordinates: {}".format(new_coordinates2))

                    new_primer2, created =  Models.PrimerDetails.objects.update_or_create(
                        name = primer_name2, gene = gene, sequence = sequence2, 
                        gc_percent = gc_percent2, tm = tm2, pairs = new_pair,
                        comments =  comments2, arrival_date = arrival_date2,
                        location = location2, status = new_status2, 
                        scientist = new_scientist, pcr_program = new_pcr, 
                        buffer = new_buffer, coordinates = new_coordinates2,
                        snp_status = snp_status2, snp_info = ";".join(snp_info2), snp_date = snp_date2
                    )
                    
                    logger.info("Created primer: {} {}".format(new_primer2.id, new_primer2))
                    logger.info(" - Primer gene: {}".format(new_primer2.gene))
                    logger.info(" - Primer sequence: {}".format(new_primer2.sequence))
                    logger.info(" - Primer gc %: {}".format(new_primer2.gc_percent))
                    logger.info(" - Primer tm: {}".format(new_primer2.tm))

                    # success save message passed to submit.html
                    messages.success(request, 'Primers successfully saved', extra_tags="success")

                    multiple_mapping(new_primer1, new_primer2, sequence1, sequence2, gene_chrom)

                    # recreate the empty forms
                    primer_form1 = Forms.PrimerForm()
                    sequence_form1 = Forms.SequenceForm()
                    status_form1 = Forms.StatusLocationForm()
                    arrival_date_form1 = Forms.ArrivalDateForm()

                    primer_form2 = Forms.PrimerForm()
                    sequence_form2 = Forms.SequenceForm()
                    status_form2 = Forms.StatusLocationForm()
                    arrival_date_form2 = Forms.ArrivalDateForm()

                else:
                    messages.error(request, "One of the primers didn't map", extra_tags="error")
                    logger.error("One of the primers didn't map")

            else:
                messages.error(request, "Can't have the same names for both primers", extra_tags="error")
                logger.error("Can't have same names for both primers")

        else:
            messages.error(request, "At least one of the forms is invalid", extra_tags="error")
            logger.error("At least one of the forms is invalid")

    else:
        print("just displaying form, data not sent")
        # if data is not sent, just display the form
        primer_form1 = Forms.PrimerForm(prefix = "form1")
        sequence_form1 = Forms.SequenceForm(prefix = "form1")
        status_form1 = Forms.StatusLocationForm(prefix = "form1")
        arrival_date_form1 = Forms.ArrivalDateForm(prefix = "form1")

        primer_form2 = Forms.PrimerForm(prefix = "form2")
        sequence_form2 = Forms.SequenceForm(prefix = "form2")
        status_form2 = Forms.StatusLocationForm(prefix = "form2")
        arrival_date_form2 = Forms.ArrivalDateForm(prefix = "form2")

            
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
        primer_form = Forms.PrimerForm(request.POST)
        sequence_form = Forms.SequenceForm(request.POST)
        status_form = Forms.StatusLocationForm(request.POST)
        arrival_date_form = Forms.ArrivalDateForm(request.POST)

        primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)

        logger.info("Editing primer")
        logger.info("Data submitted by scientist:")

        for field, value in request.POST.items():
            if field != "csrfmiddlewaretoken" or "button" not in field:
                logger.info(" - {}: {}".format(field, value))

        # when update button is pressed, save updates made to current primer
        if request.POST.get("update_primer_button"):
            if (primer_form.is_valid() and 
                sequence_form.is_valid() and
                status_form.is_valid() and
                arrival_date_form.is_valid()
            ):
                # the form is valid
                primer_name = primer_form.cleaned_data["name"]
                gene = primer_form.cleaned_data["gene"] 
                sequence = sequence_form.cleaned_data["sequence"]
                status = status_form.cleaned_data["status"]
                comments = primer_form.cleaned_data["comments"]
                arrival_date = arrival_date_form.cleaned_data["arrival_date"]
                buffer = primer_form.cleaned_data["buffer"].capitalize()
                pcr_program = primer_form.cleaned_data["pcr_program"]
                forename = primer_form.cleaned_data["forename"].capitalize()
                surname = primer_form.cleaned_data["surname"].capitalize()
                location = status_form.cleaned_data["location"]

                # save primer to database
                new_status, created = Models.Status.objects.update_or_create(name = status)
                logger.info("Using status: {}".format(new_status))

                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                if created:
                    logger.info("New scientist added to db: {}".format(new_scientist))
                else:
                    logger.info("Scientist submitting primer: {}".format(new_scientist))

                new_pcr, created = Models.PCRProgram.objects.update_or_create(
                    name = pcr_program)

                if created:
                    logger.info("New pcr program added to db: {}".format(new_pcr))
                else:
                    logger.info("Using pcr program: {}".format(new_pcr))

                new_buffer, created = Models.Buffer.objects.update_or_create(name = buffer)

                if created:
                    logger.info("New buffer added to db: {}".format(new_buffer))
                else:
                    logger.info("Using buffer: {}".format(new_buffer))

                # if primer is present updates, if not creates new instance in database
                new_primer, created =  Models.PrimerDetails.objects.update_or_create(
                    name = primer_name, defaults={
                        'gene' : gene, 'sequence': sequence, 
                        'comments':  comments, 'arrival_date': arrival_date,
                        'location': location, 'status': new_status, 
                        'scientist': new_scientist,'pcr_program': new_pcr, 
                        'buffer': new_buffer
                })

                logger.info("Updating primer: {} {}".format(new_primer.id, new_primer))
                logger.info(" - Primer gene: {}".format(new_primer.gene))
                logger.info(" - Primer sequence: {}".format(new_primer.sequence))
                logger.info(" - Primer gc %: {}".format(new_primer.gc_percent))
                logger.info(" - Primer tm: {}".format(new_primer.tm))

                messages.success(request, 'Primer "{}" successfully updated'.format(new_primer),
                    extra_tags="success")
               
                return  redirect('/primer_db/')

            else:
                # view for form with populated data from selected primer if form is invalid
                primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)[0]

                context_dict["primer_form"] = primer_form
                context_dict["sequence_form"] = sequence_form
                context_dict["status_form"] = status_form
                context_dict["arrival_date_form"] = arrival_date_form

                return render(request, 'primer_db/edit_primer.html', context_dict)

        # when delete button is pressed, delete current primer
        elif request.POST.get("delete_primer_button"):
            messages.success(request, 'Primer "{}" successfully deleted'.format(primer[0]),
                extra_tags="success")

            logger.info("Deleting {}".format(primer[0]))
            
            primer[0].delete()

            return  redirect('/primer_db/')
    
        elif request.POST.get("check_snp_primer_button"):
            primer.update(snp_status = 3)
            primer.update(snp_date = timezone.now())

            logger.info("SNP checking: {}".format(primer[0]))

            messages.success(
                request, 'SNP checked primer "{}"'.format(primer[0]),
                extra_tags="success"
            )

            return redirect('/primer_db/')

        elif request.POST.get("update_date_button"):
            primer.update(last_date_used = timezone.now())

            logger.info("Updating last date used: {}".format(primer[0]))
            
            messages.success(
                request, 'Last date used for primer "{}" successfully updated'.format(primer[0]),
                extra_tags="success"
            )

            return redirect('/primer_db/')

    primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)[0]
    coordinates = primer.coordinates
    status = primer.status

    primer_details_dict = {
        'name' : primer.name,
        'gene' : primer.gene,
        'gc_percent' : primer.gc_percent,
        'tm' : primer.tm,
        'comments' : primer.comments,
        'location' : primer.location,
        'buffer' : primer.buffer,
        'pcr_program' : primer.pcr_program,
        'forename' : primer.scientist.forename,
        'surname' : primer.scientist.surname,
        'snp_date' : primer.snp_date,
        'snp_info' : primer.snp_info
    }

    primer_form = Forms.PrimerForm(initial = primer_details_dict)
    sequence_form = Forms.SequenceForm(initial = model_to_dict(primer))
    location_form = Forms.StatusLocationForm(initial = model_to_dict(primer))
    arrival_date_form = Forms.ArrivalDateForm(initial = model_to_dict(primer))
    status_form =  Forms.StatusLocationForm(initial = model_to_dict(status))

    context_dict["primer_form"] = primer_form
    context_dict["sequence_form"] = sequence_form
    context_dict["location_form"] = location_form
    context_dict["arrival_date_form"] = arrival_date_form
    context_dict["status_form"] = status_form

    context_dict["primer"] = primer

    if primer.snp_info:
        context_dict["snps"] = []

        for snp_info in primer.snp_info.split(";"):
            data = []
            for ele in snp_info.split(","):
                if "?" not in ele:
                    data.append(ele.strip())
                else:
                    for stuff in ele.split("?"):
                        data.append(stuff.strip())

            context_dict["snps"].append(data)
    else:
        context_dict["snps"] = None

    return render(request, 'primer_db/edit_primer.html', context_dict)


def edit_pair(request, PrimerDetails_id):
    """
    Function for edit view of a pair of primers
    """

    context_dict = {}

    if request.method == "POST":
        # trick to fool form2
        data = request.POST.copy()
        data["form2-buffer"] = data["form1-buffer"]
        data["form2-gene"] = data["form1-gene"]
        data["form2-pcr_program"] = data["form1-pcr_program"]
        data["form2-forename"] = data["form1-forename"]
        data["form2-surname"] = data["form1-surname"]

        # data sent for first primer
        primer_form1 = Forms.PrimerForm(request.POST, prefix ="form1")
        sequence_form1 = Forms.SequenceForm(request.POST, prefix ="form1")
        status_loc_form1 = Forms.StatusLocationForm(request.POST, prefix ="form1")
        arrival_date_form1 = Forms.ArrivalDateForm(request.POST, prefix ="form1")

        # data sent for second primer
        primer_form2 = Forms.PrimerForm(data, prefix ="form2")
        sequence_form2 = Forms.SequenceForm(request.POST, prefix ="form2")
        status_loc_form2 = Forms.StatusLocationForm(request.POST, prefix ="form2")
        arrival_date_form2 = Forms.ArrivalDateForm(request.POST, prefix ="form2")

        list_forms = [primer_form1, sequence_form1, status_loc_form1, arrival_date_form1,
                      primer_form2, sequence_form2, status_loc_form2, arrival_date_form2]

        # data for first primer
        context_dict["primer_form1"] = primer_form1
        context_dict["sequence_form1"] = sequence_form1
        context_dict["arrival_date_form1"] = arrival_date_form1
        context_dict["status_loc_form1"] = status_loc_form1

        # data for second primer
        context_dict["primer_form2"] = primer_form2
        context_dict["sequence_form2"] = sequence_form2
        context_dict["arrival_date_form2"] = arrival_date_form2
        context_dict["status_loc_form2"] = status_loc_form2

        logger.info("Editing primer pair")
        logger.info("Data submitted by scientist:")

        for field, value in data.items():
            if field != "csrfmiddlewaretoken" or "button" not in field:
                logger.info(" - {}: {}".format(field, value))

        # check selected primer id
        primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)[0]

        if primer.pairs_id:
            # if primer is from a pair and to be edited in pair form
            primer1, primer2 = Models.PrimerDetails.objects.filter(pairs_id = primer.pairs_id)
            context_dict["primer2"] = primer2        

        context_dict["primer1"] = primer1

        fields = ["name", "gene", "sequence", "buffer", "pcr_program", "arrival_date", "status", 
            "location", "comments", "forename", "surname"
        ]

        # when update button is pressed, save updates made to current primer
        if request.POST.get("update_primers_button"):
            if (primer_form1.is_valid() and 
                sequence_form1.is_valid() and
                status_loc_form1.is_valid() and
                arrival_date_form1.is_valid() and
                
                primer_form2.is_valid() and 
                sequence_form2.is_valid() and
                status_loc_form2.is_valid() and
                arrival_date_form2.is_valid()
            ):
                forms1 = []
                forms2 =[]

                # loop for adding correct fields to forms
                for field in fields:
                    if field == "sequence":
                        forms1.append(sequence_form1.cleaned_data[field])
                        forms2.append(sequence_form2.cleaned_data[field])
                    elif field == "status" or field == "location":
                        forms1.append(status_loc_form1.cleaned_data[field])
                        forms2.append(status_loc_form2.cleaned_data[field])
                    elif field == "arrival_date":
                        forms1.append(arrival_date_form1.cleaned_data[field])
                        forms2.append(arrival_date_form2.cleaned_data[field])
                    else:
                        forms1.append(primer_form1.cleaned_data[field])
                        forms2.append(primer_form2.cleaned_data[field])  

                # unpack variables for first form and save to db
                (primer_name, gene, sequence, buffer, pcr_program, arrival_date, status, 
                 location, comments, forename, surname) = forms1

                logger.info("Updating {}".format(primer1[0]))

                new_status, created = Models.Status.objects.update_or_create(name = status)
                logger.info("Using status: {}".format(new_status))

                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                if created:
                    logger.info("New scientist added to db: {}".format(new_scientist))
                else:
                    logger.info("Scientist who submitted primer: {}".format(new_scientist))

                new_pcr, created = Models.PCRProgram.objects.update_or_create(name = pcr_program)

                if created:
                    logger.info("New pcr program added to db: {}".format(new_pcr))
                else:
                    logger.info("Using pcr program: {}".format(new_pcr))

                new_buffer, created = Models.Buffer.objects.update_or_create(name = buffer)

                if created:
                    logger.info("New buffer added to db: {}".format(new_buffer))
                else:
                    logger.info("Using buffer: {}".format(new_buffer))

                new_primer =  Models.PrimerDetails.objects.update_or_create(
                    name = primer_name, defaults={
                        'gene' : gene, 'sequence': sequence, 
                        'comments':  comments, 'arrival_date': arrival_date,'location': location, 
                        'status': new_status, 'scientist': new_scientist,'pcr_program': new_pcr, 
                        'buffer': new_buffer
                    }
                )

                logger.info("Updating primer: {} {}".format(new_primer.id, new_primer))
                logger.info(" - Primer gene: {}".format(new_primer.gene))
                logger.info(" - Primer sequence: {}".format(new_primer.sequence))
                logger.info(" - Primer gc %: {}".format(new_primer.gc_percent))
                logger.info(" - Primer tm: {}".format(new_primer.tm))

                # unpack variables for second form and save to db
                (primer_name, gene, sequence, buffer, pcr_program, arrival_date, status, 
                 location, comments, forename, surname) = forms2

                logger.info("Updating {}".format(primer2[0]))

                new_status, created = Models.Status.objects.update_or_create(name = status)
                logger.info("Using status: {}".format(new_status))

                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                new_pcr, created = Models.PCRProgram.objects.update_or_create(name = pcr_program)

                new_buffer, created = Models.Buffer.objects.update_or_create(name = buffer)

                new_primer =  Models.PrimerDetails.objects.update_or_create(
                    name = primer_name, defaults={
                        'gene' : gene, 'sequence': sequence, 
                        'comments':  comments, 'arrival_date': arrival_date,'location': location, 
                        'status': new_status, 'scientist': new_scientist,'pcr_program': new_pcr, 
                        'buffer': new_buffer
                    }
                )

                logger.info("Updating primer: {} {}".format(new_primer.id, new_primer))
                logger.info(" - Primer gene: {}".format(new_primer.gene))
                logger.info(" - Primer sequence: {}".format(new_primer.sequence))
                logger.info(" - Primer gc %: {}".format(new_primer.gc_percent))
                logger.info(" - Primer tm: {}".format(new_primer.tm))

                # for displaying success message
                primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)[0]
                primer_pair = primer.pairs_id
                primer1, primer2 = Models.PrimerDetails.objects.filter(pairs_id = primer.pairs_id)

                messages.success(request, 'Primer "{}" and "{}" successfully updated'.format(primer1, primer2),
                    extra_tags="success")

                return  redirect('/primer_db/')

            else:
                for form in list_forms:
                    if not form.is_valid():
                        error = form.errors["__all__"]
                        messages.add_message(
                            request,
                            messages.ERROR,
                            error,
                            extra_tags='error'
                        )

                return render(request, 'primer_db/edit_pair.html', context_dict)

        elif request.POST.get("check_snp_primer1_button") or request.POST.get("check_snp_primer2_button"):
            checked_primer1 = request.POST.get("check_snp_primer1_button", None)
            checked_primer2 = request.POST.get("check_snp_primer2_button", None)

            if checked_primer1:
                primer = Models.PrimerDetails.objects.filter(name = checked_primer1)
            elif checked_primer2:
                primer = Models.PrimerDetails.objects.filter(name = checked_primer2)

            logger.info("SNP checking {}".format(primer[0]))

            primer.update(snp_status = 3)
            primer.update(snp_date = timezone.now())

        elif request.POST.get("update_date_button"):
            queryset_primer1 = Models.PrimerDetails.objects.filter(pk = primer1.id)
            queryset_primer2 = Models.PrimerDetails.objects.filter(pk = primer2.id)

            logger.info("Updating last date used for {} and {}".format(queryset_primer1[0], queryset_primer2[0]))

            queryset_primer1.update(last_date_used = timezone.now())
            queryset_primer2.update(last_date_used = timezone.now())
            
            messages.success(
                request, 'Last date used for primer "{}" and "{}" successfully updated'.format(
                    queryset_primer1[0], queryset_primer2[0]
                    ),
                extra_tags="success")

            return redirect('/primer_db/')

    # check selected primer id
    primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)[0]

    if primer.pairs_id:
        # if primer is from a pair and to be edited in pair form
        primer1, primer2 = Models.PrimerDetails.objects.filter(pairs_id = primer.pairs_id)
    else:
        # if primer has no associated pair, render single edit page with selected primer
        return redirect('edit_primer', PrimerDetails_id = PrimerDetails_id)

    primer1_details_dict = {
        'name' : primer1.name, 'gene' : primer1.gene,
        'comments' : primer1.comments, 'buffer' : primer1.buffer,
        'pcr_program' : primer1.pcr_program, 'forename' : primer1.scientist.forename,
        'surname' : primer1.scientist.surname
    }

    primer2_details_dict = {
        'name' : primer2.name, 'gene' : primer2.gene,
        'comments' : primer2.comments, 'buffer' : primer2.buffer,
        'pcr_program' : primer2.pcr_program, 'forename' : primer2.scientist.forename,
        'surname' : primer2.scientist.surname
    }

    primer_form1 = Forms.PrimerForm(initial = primer1_details_dict, prefix = "form1")
    sequence_form1 = Forms.SequenceForm(initial = model_to_dict(primer1), prefix = "form1")
    arrival_date_form1 = Forms.ArrivalDateForm(initial = model_to_dict(primer1), prefix = "form1")
    status_loc_form1 = Forms.StatusLocationForm(initial = model_to_dict(primer1), prefix = "form1")

    # data for second primer
    primer_form2 = Forms.PrimerForm(initial = primer2_details_dict, prefix = "form2")
    sequence_form2 = Forms.SequenceForm(initial = model_to_dict(primer2), prefix = "form2")
    arrival_date_form2 = Forms.ArrivalDateForm(initial = model_to_dict(primer2), prefix = "form2")
    status_loc_form2 = Forms.StatusLocationForm(initial = model_to_dict(primer2), prefix = "form2")

    # data for first primer
    context_dict["primer_form1"] = primer_form1
    context_dict["sequence_form1"] = sequence_form1
    context_dict["arrival_date_form1"] = arrival_date_form1
    context_dict["status_loc_form1"] = status_loc_form1

    # data for second primer
    context_dict["primer_form2"] = primer_form2
    context_dict["sequence_form2"] = sequence_form2
    context_dict["arrival_date_form2"] = arrival_date_form2
    context_dict["status_loc_form2"] = status_loc_form2

    context_dict["primer1"] = primer1

    if primer1.snp_info:
        context_dict["snp1"] = []

        for snp_info in primer1.snp_info.split(";"):
            data = []
            for ele in snp_info.split(","):
                if "?" not in ele:
                    data.append(ele.strip())
                else:
                    for stuff in ele.split("?"):
                        data.append(stuff.strip())

            context_dict["snp1"].append(data)
    else:
        context_dict["snp1"] = None

    context_dict["primer2"] = primer2

    if primer2.snp_info:
        context_dict["snp2"] = []

        for snp_info in primer2.snp_info.split(";"):
            data = []
            for ele in snp_info.split(","):
                if "?" not in ele:
                    data.append(ele.strip())
                else:
                    for stuff in ele.split("?"):
                        data.append(stuff.strip())

            context_dict["snp2"].append(data)
    else:
        context_dict["snp2"] = None

    return render(request, 'primer_db/edit_pair.html', context_dict)