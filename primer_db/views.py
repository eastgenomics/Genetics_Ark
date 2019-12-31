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
import time

import primer_db.forms as Forms
import primer_db.models as Models

# path to mapping script
sys.path.insert(1, '/mnt/storage/home/rainfoj/Projects/primer_mapper/bin/') 
import primer_mapper

sys.path.insert(1, '/mnt/storage/home/kimy/projects/primer_database/genetics_ark_django/utils/') 
import gnomAD_queries
import snp_check


# setup the logging
logging.config.dictConfig({
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'normal': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s'
        }
    },
    'handlers': {
        'submitting': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'normal',
            'filename': 'primer_db/logs/submitting.log',
            'mode': 'a',
            'maxBytes': 10000000,
            'backupCount': 5,
        },
        'editing': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'normal',
            'filename': 'primer_db/logs/editing.log',
            'mode': 'a',
            'maxBytes': 10000000,
            'backupCount': 5,
        },
        'deleting': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'normal',
            'filename': 'primer_db/logs/deleting.log',
            'mode': 'a',
            'maxBytes': 10000000,
            'backupCount': 5,
        },
        'index': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'normal',
            'filename': 'primer_db/logs/index.log',
            'mode': 'a',
            'maxBytes': 10000000,
            'backupCount': 5,
        }        
    },
    'loggers': {
        'submitting': {
            'level': 'DEBUG',
            'handlers': ['submitting']
        },
        'editing': {
            'level': 'DEBUG',
            'handlers': ['editing']
        },
        'deleting': {
            'level': 'DEBUG',
            'handlers': ['deleting']
        },
        'index': {
            'level': 'DEBUG',
            'handlers': ['index']
        }
    }
})


# 4 different loggers for the actions possibles in the interface
logger_submit = logging.getLogger("submitting")
logger_editing = logging.getLogger("editing")
logger_deleting = logging.getLogger("deleting")
logger_index = logging.getLogger("index")


def mapper1(seq, gene, ref):
    """
    Function for calling primer mapper when submitting single primer
    """
    mapping_result = primer_mapper.main(seq, gene, ref)

    return mapping_result


def mapper2(primer_seq1, gene, ref, primer_seq2):
    """
    Function for calling primer mapper when submitting pair of primers
    """
    mapping_result = primer_mapper.main(primer_seq1, gene, ref, primer_seq2)

    return mapping_result


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


def index(request):
    """
    Homepage view of database; displays all primers inc. search functions and use of check boxes for changing
    status of multiple primers and recalculating coverage for a given pair of primers
    """

    context_dict = {}
    filtered_dict = {}
    filtering = False

    # function for filtering primers that have coverage for the given variant position  
    if request.method == 'POST':
        # list of id for the primers checked in the main table
        name_filter = request.POST.get("name_filter", None)
        gene_filter = request.POST.get("gene_filter", None)
        pks = request.POST.getlist('check')

        filter_grch37 = Models.PrimerDetails.objects.none()
        filter_grch38 = Models.PrimerDetails.objects.none()
        filter_name = Models.PrimerDetails.objects.none()
        filter_gene = Models.PrimerDetails.objects.none()

        if 'search_snp' in request.POST:
            var_pos = request.POST.get("var_pos", None)
            chrom_no = request.POST.get("chrom_no", None)

            # filtering using the position
            filtering = True
            primers37 = []
            primers38 = []

            bugged_primers = []

            var_pos = int(var_pos)

            # get the id and coverage for all primers on given chromosome
            position_filtered_primers = Models.PrimerDetails.objects.filter(coordinates__chrom_no = chrom_no)
            
            for primer in position_filtered_primers:
                coordinates = primer.coordinates

                if primer.pairs_id:
                    pair = Models.PrimerDetails.objects.filter(pairs_id = primer.pairs_id)

                    if len(pair) == 2:
                        primer1, primer2 = pair

                    else:
                        bugged_primers.append((primer.id, primer))
                        continue

                    coordinates_37 = [
                        primer1.coordinates.start_coordinate_37, primer1.coordinates.end_coordinate_37,
                        primer2.coordinates.start_coordinate_37, primer2.coordinates.end_coordinate_37
                    ]

                    coordinates_38 = [
                        primer1.coordinates.start_coordinate_38, primer1.coordinates.end_coordinate_38,
                        primer2.coordinates.start_coordinate_38, primer2.coordinates.end_coordinate_38
                    ]

                    if min(coordinates_37) <= var_pos <= max(coordinates_37):
                        primers37.append(primer1.id)
                        primers37.append(primer2.id)

                    if min(coordinates_38) <= var_pos <= max(coordinates_38):
                        primers38.append(primer1.id)
                        primers38.append(primer2.id)                        
                    
                else:
                    # check if variant is in a primer sequence
                    if coordinates.start_coordinate_37 <= var_pos <= coordinates.end_coordinate_37:
                        primers37.append(primer.id)

                    if coordinates.start_coordinate_38 <= var_pos <= coordinates.end_coordinate_38:
                        primers38.append(primer.id)

            # get query set for primer IDs that cover the variant position
            filter_grch37 = Models.PrimerDetails.objects.filter(pk__in=primers37)
            filter_grch38 = Models.PrimerDetails.objects.filter(pk__in=primers38)

            filtered_dict["pos"] = primers37 + primers38
            request.session["filtered_dict"] = filtered_dict

            if bugged_primers:
                logger_index.error("There are pair ids that are bugged")

                for id_, primer in bugged_primers:
                    logger_index.error(" - {} {}".format(id_, primer))

                messages.add_message(request,
                    messages.ERROR,
                    "Please contact BioinformaticsTeamGeneticsLab@addenbrookes.nhs.uk as the filtering skipped {} primers".format(len(bugged_primers)),
                    extra_tags="alert-danger"
                )

        elif "filter_button" in request.POST:
            filter_params = {}
            
            for field, value in request.POST.items():
                if field.endswith("filter") and value:
                    if field == "chr_filter":
                        filter_params["coordinates__chrom_no"] = value
                    elif field == "status_filter":
                        filter_params["status__name"] = value
                    elif field == "name_filter":
                        filter_params["name__icontains"] = value
                    elif field == "location_filter":
                        filter_params["location__icontains"] = value
                    else:
                        filter_params[field.split("_")[0]] = value

            filtered_primers = Models.PrimerDetails.objects.filter(**filter_params)

            filtered_dict["filter"] = [primer.id for primer in filtered_primers]
            request.session['filtered_dict'] = filtered_dict

            context_dict["nb_primers"] = len(filtered_primers)
            context_dict["not_check"] = len([primer for primer in filtered_primers if primer.snp_status == "0"])
            context_dict["passed_check"] = len([primer for primer in filtered_primers if primer.snp_status == "1"])
            context_dict["failed_check"] = len([primer for primer in filtered_primers if primer.snp_status == "2"])
            context_dict["manually_checked"] = len([primer for primer in filtered_primers if primer.snp_status == "3"])
            context_dict["not_in_gnomAD"] = len([primer for primer in filtered_primers if primer.snp_status == "4"])

            primers = filtered_primers
            table = PrimerDetailsTable(primers)

        elif 'recalc' in request.POST:
            amplicon_length_37 = None
            amplicon_length_38 = None
            recalc_msg = []

            if len(pks) != 2:
                messages.error(request, '{} primers selected, please select 2 primers'.format(len(pks)), extra_tags='alert-danger')
                return redirect('/primer_db/')

            gene1 = Models.PrimerDetails.objects.values_list('gene', flat=True).get(pk=pks[0])
            gene2 = Models.PrimerDetails.objects.values_list('gene', flat=True).get(pk=pks[1])

            if gene1 != gene2:
                msg = "2 different genes ({}, {}) for the primer coverage calculation".format(gene1, gene2)
                messages.error(request, msg, extra_tags='alert-danger')
                return redirect('/primer_db/')

            primer1 = Models.PrimerDetails.objects.get(pk = pks[0])
            primer2 = Models.PrimerDetails.objects.get(pk = pks[1])

            recalc_msg.append("Selected primers: {} and {}".format(primer1, primer2))

            if primer1.coordinates.strand == "+" and primer2.coordinates.strand == "-":
                f_start37 = primer1.coordinates.start_coordinate_37
                r_end37 = primer2.coordinates.end_coordinate_37
                f_start38 = primer1.coordinates.start_coordinate_38
                r_end38 = primer2.coordinates.end_coordinate_38

                coverage37 = "{}:{}-{}".format(primer1.coordinates.chrom_no, f_start37, r_end37)
                coverage38 = "{}:{}-{}".format(primer1.coordinates.chrom_no, f_start38, r_end38)

                recalc_msg.append("{} is forward and {} is reverse".format(primer1, primer2))

            elif primer2.coordinates.strand == "+" and primer1.coordinates.strand == "-":
      
                f_start37 = primer2.coordinates.start_coordinate_37
                r_end37 = primer1.coordinates.end_coordinate_37
                f_start38 = primer2.coordinates.start_coordinate_38
                r_end38 = primer1.coordinates.end_coordinate_38

                coverage37 = "{}:{}-{}".format(primer1.coordinates.chrom_no, f_start37, r_end37)
                coverage38 = "{}:{}-{}".format(primer1.coordinates.chrom_no, f_start38, r_end38)

                recalc_msg.append("{} is forward and {} is reverse".format(primer2, primer1))

            else:
                msg = "You need a forward and a reverse primer"
                messages.error(request, msg, extra_tags='alert-danger')
                return redirect('/primer_db/')

            amplicon_length_37 = r_end37 - f_start37
            amplicon_length_38 = r_end38 - f_start38

            recalc_msg.append("Recalculated coverage for GRCh37 is: {}".format(coverage37))
            
            recalc_msg.append("Recalculated coverage for GRCh38 is: {}".format(coverage38))

            if amplicon_length_37 < 0:
                recalc_msg.append("Amplification not possible in GRCh37 with this pair of primer")

            if amplicon_length_38 < 0:
                recalc_msg.append("Amplification not possible in GRCh38 with this pair of primer")

            recalc_msg.append("Amplicon length in GRCh37 is: {}".format(amplicon_length_37))
            recalc_msg.append("Amplicon length in GRCh38 is: {}".format(amplicon_length_38))

            logger_index.info("Recalculating for {} and {}".format(primer1, primer2))

            primers = Models.PrimerDetails.objects.all()
            table = PrimerDetailsTable(primers)
            context_dict["recalc"] = recalc_msg

        elif 'change_status' in request.POST:
            new_status = request.POST.get('new_status') # get status to change to from POST data

            for pk in pks:
                update_status, created = Models.Status.objects.get_or_create(name=new_status)
                primer = Models.PrimerDetails.objects.get(pk=pk)
                primer.status = update_status
                primer.save()

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    "Updating {} status to {}".format(primer, new_status),
                    extra_tags='alert-success'
                )

                logger_index.info("Changing status for {} to {}".format(primer, update_status))

            filtered_dict = request.session.get('filtered_dict', None)

            if filtered_dict:
                primers = Models.PrimerDetails.objects.filter(pk__in = filtered_dict["filter"])
                table = PrimerDetailsTable(primers)

        elif 'failed_snp_check' in request.POST or "manually_snp_check" in request.POST or "not_recognized_snp_check" in request.POST:
            if "failed_snp_check" in request.POST:
                status = "2"
            elif "manually_snp_check" in request.POST:
                status = "3"
            elif "not_recognized_snp_check" in request.POST:
                status = "4"

            filtered = request.session.get("filtered_dict", None)

            if filtered:               
                primers = Models.PrimerDetails.objects.filter(pk__in=filtered["filter"], snp_status=status)
            else:
                primers = Models.PrimerDetails.objects.all().filter(snp_status = status)

            primer_ids = [primer.id for primer in primers]

            request.session["primer_ids_snp"] = primer_ids

            table = PrimerDetailsTable(primers)

    else:
        filtered_dict = request.session.get("filtered_dict", None)
        filtered_snps = request.session.get("primer_ids_snp", None)

        if filtered_snps and "page" in request.GET:
            primer_ids = filtered_snps
            primers = Models.PrimerDetails.objects.filter(pk__in = primer_ids)

        elif filtered_dict and "page" in request.GET:
            primer_ids = []

            for type_ in ["name", "gene", "pos"]:
                if type_ in filtered_dict:
                    primer_ids += filtered_dict[type_]

            primers = Models.PrimerDetails.objects.filter(pk__in = primer_ids)

        else:
            primers = Models.PrimerDetails.objects.all()

            if filtered_snps:
                del request.session["primer_ids_snp"]

            if filtered_dict:
                del request.session["filtered_dict"]

        table = PrimerDetailsTable(primers)

    # returns primer totals filtered by status for displaying on main db view
    total_archived = Models.PrimerDetails.objects.filter(status__name__icontains="archived").count()
    total_bank = Models.PrimerDetails.objects.filter(status__name__icontains="bank").count()
    total_order = Models.PrimerDetails.objects.filter(status__name__icontains="order").count()

    context_dict["table"] = table
    context_dict["total_archived"] = total_archived
    context_dict["total_bank"] = total_bank
    context_dict["total_order"] = total_order

    context_dict["nb_primers"] = len(primers)
    context_dict["not_check"] = len([primer for primer in primers if primer.snp_status == "0"])
    context_dict["passed_check"] = len([primer for primer in primers if primer.snp_status == "1"])
    context_dict["failed_check"] = len([primer for primer in primers if primer.snp_status == "2"])
    context_dict["manually_checked"] = len([primer for primer in primers if primer.snp_status == "3"])
    context_dict["not_in_gnomAD"] = len([primer for primer in primers if primer.snp_status == "4"])

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

        context_dict["primer_form"] = primer_form
        context_dict["sequence_form"] = sequence_form
        context_dict["status_form"] = status_form
        context_dict["arrival_date_form"] = arrival_date_form

        logger_submit.info("Submitting primer")
        logger_submit.info("Data submitted by scientist:")

        for field, value in request.POST.items():
            if field != "csrfmiddlewaretoken" and "button" not in field:
                logger_submit.info(" - {}: {}".format(field, value.strip()))

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

            # check if the name of primer is already in the database
            if Models.PrimerDetails.objects.filter(name=name):
                messages.error(request, "Primer name {} already exists".format(name), extra_tags= "alert-danger")
                return render(request, 'primer_db/submit.html', context_dict)

            # call functions to calculate gc % and tm
            gc_percent = gc_calculate(sequence)
            tm = tm_calculate(sequence)

            # call primer_mapper to map primer to both 37 and 38, then return coords and chromosome number
            mapping_37 = mapper1(sequence, gene, 37)
            mapping_38 = mapper1(sequence, gene, 38)

            if mapping_37 and mapping_38:
                start_coordinate_37, end_coordinate_37, gene_chrom, strand = mapping_37
                start_coordinate_38, end_coordinate_38, gene_chrom, strand = mapping_38
            else:
                messages.error(request, "Gene {} not found for mapping, please check gene name".format(gene), extra_tags= "alert-danger")
                return render(request, "primer_db/submit.html", context_dict)

            if all((start_coordinate_37, end_coordinate_37, start_coordinate_38, end_coordinate_38)):
                # call function to check for SNPs
                snp_status, snp_date, snp_info = snp_check.main(
                    gene, start_coordinate_37, end_coordinate_37,
                    start_coordinate_38, end_coordinate_38
                )

                if snp_info:
                    logger_submit.info("Detected snps in primer")
                else:
                    logger_submit.info("No snps detected")

                # save primer to database
                status_object = Models.Status.objects.filter(name = status)[0]

                logger_submit.info("Using status: {}".format(status_object))

                new_scientist, created = Models.Scientist.objects.get_or_create(
                    forename = forename, surname = surname)

                if created:
                    logger_submit.info("New scientist added to db: {}".format(new_scientist))
                else:
                    logger_submit.info("Scientist submitting primer: {}".format(new_scientist))

                new_pcr, created = Models.PCRProgram.objects.get_or_create(
                    name = pcr_program)

                if created:
                    logger_submit.info("New pcr program added to db: {}".format(new_pcr))
                else:
                    logger_submit.info("Using pcr program: {}".format(new_pcr))

                new_buffer, created = Models.Buffer.objects.get_or_create(name = buffer)

                if created:
                    logger_submit.info("New buffer added to db: {}".format(new_buffer))
                else:
                    logger_submit.info("Using buffer: {}".format(new_buffer))

                new_coordinates, created = Models.Coordinates.objects.get_or_create(
                    start_coordinate_37 = start_coordinate_37, end_coordinate_37 = end_coordinate_37,
                    start_coordinate_38 = start_coordinate_38, end_coordinate_38 = end_coordinate_38, 
                    chrom_no = gene_chrom, strand = strand
                    )

                if created:
                    logger_submit.info("New coordinates added to db: {}".format(new_coordinates))
                else:
                    logger_submit.info("Using coordinates: {}".format(new_coordinates))

                new_primer = Models.PrimerDetails.objects.create(
                    name = name, gene = gene, sequence = sequence, 
                    gc_percent = gc_percent, tm = tm,
                    comments =  comments, arrival_date = arrival_date,
                    location = location, snp_status = snp_status,
                    snp_date = snp_date, snp_info = ";".join(snp_info),
                    status = status_object, scientist = new_scientist, 
                    pcr_program = new_pcr, buffer = new_buffer, 
                    coordinates = new_coordinates)

                logger_submit.info("Created primer: {} {}".format(new_primer.id, new_primer))
                logger_submit.info(" - Primer gene: {}".format(new_primer.gene))
                logger_submit.info(" - Primer sequence: {}".format(new_primer.sequence))
                logger_submit.info(" - Primer gc %: {}".format(new_primer.gc_percent))
                logger_submit.info(" - Primer tm: {}".format(new_primer.tm))

                # success save message passed to submit.html
                messages.success(request, 'Primer {} successfully saved with coordinates: GRCh37 {} - {} and GRCh38 {} - {}'.format(
                    name, start_coordinate_37, end_coordinate_37, start_coordinate_38, end_coordinate_38), extra_tags="alert-success")

                return render(request, 'primer_db/submit.html', context_dict)

            else:
                messages.error(request, "The sequence provided didn't map to gene provided", extra_tags="alert-danger")
                logger_submit.error("Sequence didn't map")

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

        context_dict["primer_form1"] = primer_form1
        context_dict["sequence_form1"] = sequence_form1
        context_dict["status_form1"] = status_form1
        context_dict["arrival_date_form1"] = arrival_date_form1

        context_dict["primer_form2"] = primer_form2
        context_dict["sequence_form2"] = sequence_form2
        context_dict["status_form2"] = status_form2
        context_dict["arrival_date_form2"] = arrival_date_form2

        logger_submit.info("Submitting primer")
        logger_submit.info("Data submitted by scientist:")

        for field, value in request.POST.items():
            if field != "csrfmiddlewaretoken" and "button" not in field:
                logger_submit.info(" - {}: {}".format(field, value.strip()))

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

            existing_primers = Models.PrimerDetails.objects.filter(name__in=[primer_name1, primer_name2])

            # check if the name given for both primers already exist
            if existing_primers:
                messages.error(request, "Primer name {} already exists".format(", ".join([primer.name for primer in existing_primers])), extra_tags="alert-danger")
                return render(request, "primer_db/submit_pair.html", context_dict)

            if primer_name1 != primer_name2:
                # call functions to calculate gc % and tm
                gc_percent1 = gc_calculate(sequence1)
                tm1 = tm_calculate(sequence1)

                gc_percent2 = gc_calculate(sequence2)
                tm2 = tm_calculate(sequence2)

                # call primer_mapper to map primer to both 37 and 38, then return coords and chromosome number
                mapping_37 = mapper2(sequence1, gene, 37, sequence2)
                mapping_38 = mapper2(sequence1, gene, 38, sequence2)

                if mapping_37 and mapping_38:
                    (coverage_37, primer1_start_37, primer1_end_37,
                     primer2_start_37, primer2_end_37, gene_chrom,
                     primer1_strand, primer2_strand) = mapping_37

                    (coverage_38, primer1_start_38, primer1_end_38,
                     primer2_start_38, primer2_end_38, gene_chrom,
                     primer1_strand, primer2_strand) = mapping_38
                else:
                    messages.error(request, "Gene {} not found for mapping, please check gene name".format(gene), extra_tags= "alert-danger")
                    return render(request, "primer_db/submit_pair.html", context_dict)

                if all((primer1_start_37, primer1_end_37, primer2_start_37, primer2_start_37,
                        primer1_start_38, primer1_end_38, primer2_start_38, primer2_end_38)
                ):
                    logger_submit.info("Common info for primers:")

                    amplicon_37 = coverage_37.split(":")[1].split("-")
                    amplicon_38 = coverage_37.split(":")[1].split("-")

                    new_pair = Models.Pairs.objects.create(
                        coverage_37 = coverage_37, coverage_38 = coverage_38,
                        size_37 = int(max(amplicon_37)) - int(min(amplicon_37)),
                        size_38 = int(max(amplicon_38)) - int(min(amplicon_38))
                    )

                    logger_submit.info(" - Pair created, id: {}".format(new_pair.id))

                    new_scientist, created = Models.Scientist.objects.get_or_create(
                        forename = forename, surname = surname)

                    if created:
                        logger_submit.info(" - New scientist added to db: {}".format(new_scientist))
                    else:
                        logger_submit.info(" - Scientist submitting primer: {}".format(new_scientist))

                    new_pcr, created = Models.PCRProgram.objects.get_or_create(
                        name = pcr_program)

                    if created:
                        logger_submit.info(" - New pcr program added to db: {}".format(new_pcr))
                    else:
                        logger_submit.info(" - Using pcr program: {}".format(new_pcr))

                    new_buffer, created = Models.Buffer.objects.get_or_create(name = buffer)

                    if created:
                        logger_submit.info(" - New buffer added to db: {}".format(new_buffer))
                    else:
                        logger_submit.info(" - Using buffer: {}".format(new_buffer))

                    #############################################################

                    logger_submit.info("Data for primer1:")

                    snp_status1, snp_date1, snp_info1 = snp_check.main(
                        gene, primer1_start_37, primer1_end_37,
                        primer1_start_38, primer1_end_38
                    )

                    if snp_info1:
                        logger_submit.info(" - SNPs detected in primer")
                    else:
                        logger_submit.info(" - No SNPs detected in primer")

                    new_status1 = Models.Status.objects.filter(name = status1)[0]

                    logger_submit.info(" - Status of primer: {}".format(new_status1))

                    new_coordinates1, created = Models.Coordinates.objects.get_or_create(
                        start_coordinate_37 = primer1_start_37, end_coordinate_37 = primer1_end_37,
                        start_coordinate_38 = primer1_start_38, end_coordinate_38 = primer1_end_38,
                        chrom_no = gene_chrom, strand = primer1_strand
                        )

                    if created:
                        logger_submit.info(" - New coordinates added to db: {}".format(new_coordinates1))
                    else:
                        logger_submit.info(" - Using coordinates: {}".format(new_coordinates1))

                    new_primer1, created =  Models.PrimerDetails.objects.update_or_create(
                        name = primer_name1, gene = gene, sequence = sequence1, 
                        gc_percent = gc_percent1, tm = tm1, pairs = new_pair,
                        comments =  comments1, arrival_date = arrival_date1,
                        location = location1, status = new_status1, 
                        scientist = new_scientist, pcr_program = new_pcr, 
                        buffer = new_buffer, coordinates = new_coordinates1,
                        snp_status = snp_status1, snp_info = ";".join(snp_info1), snp_date = snp_date1
                    )
                    
                    logger_submit.info("Created primer: {} {}".format(new_primer1.id, new_primer1))
                    logger_submit.info(" - Primer gene: {}".format(new_primer1.gene))
                    logger_submit.info(" - Primer sequence: {}".format(new_primer1.sequence))
                    logger_submit.info(" - Primer gc %: {}".format(new_primer1.gc_percent))
                    logger_submit.info(" - Primer tm: {}".format(new_primer1.tm))

                    #############################################################

                    logger_submit.info("Data for primer2")

                    snp_status2, snp_date2, snp_info2 = snp_check.main(
                        gene, primer2_start_37, primer2_end_37,
                        primer2_start_38, primer2_end_38
                    )

                    if snp_info2:
                        logger_submit.info(" - SNPs detected in primer")
                    else:
                        logger_submit.info(" - No SNPs detected in primer")

                    # save primer 2 to database
                    new_status2, created = Models.Status.objects.get_or_create(name = status2)

                    logger_submit.info(" - Status of primer2: {}".format(new_status2))

                    new_coordinates2, created = Models.Coordinates.objects.get_or_create(
                        start_coordinate_37 = primer2_start_37, end_coordinate_37 = primer2_end_37,
                        start_coordinate_38 = primer2_start_38, end_coordinate_38 = primer2_end_38,
                        chrom_no = gene_chrom, strand = primer2_strand
                        )

                    if created:
                        logger_submit.info(" - New coordinates added to db: {}".format(new_coordinates2))
                    else:
                        logger_submit.info(" - Using coordinates: {}".format(new_coordinates2))

                    new_primer2, created =  Models.PrimerDetails.objects.update_or_create(
                        name = primer_name2, gene = gene, sequence = sequence2, 
                        gc_percent = gc_percent2, tm = tm2, pairs = new_pair,
                        comments =  comments2, arrival_date = arrival_date2,
                        location = location2, status = new_status2, 
                        scientist = new_scientist, pcr_program = new_pcr, 
                        buffer = new_buffer, coordinates = new_coordinates2,
                        snp_status = snp_status2, snp_info = ";".join(snp_info2), snp_date = snp_date2
                    )
                    
                    logger_submit.info("Created primer: {} {}".format(new_primer2.id, new_primer2))
                    logger_submit.info(" - Primer gene: {}".format(new_primer2.gene))
                    logger_submit.info(" - Primer sequence: {}".format(new_primer2.sequence))
                    logger_submit.info(" - Primer gc %: {}".format(new_primer2.gc_percent))
                    logger_submit.info(" - Primer tm: {}".format(new_primer2.tm))

                    # success save message passed to submit.html
                    messages.success(request, 'Primers {} and {} successfully saved'.format(new_primer1, new_primer2),
                        extra_tags="alert-success")

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
                    messages.error(request, "One of the primers didn't map", extra_tags="alert-danger")
                    logger_submit.error("One of the primers didn't map")

            else:
                messages.error(request, "Can't have the same names for both primers", extra_tags="alert-danger")
                logger_submit.error("Can't have same names for both primers")

        else:
            messages.error(request, "At least one of the forms is invalid", extra_tags="alert-danger")
            logger_submit.error("At least one of the forms is invalid")

    else:
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
        primer = Models.PrimerDetails.objects.get(pk = PrimerDetails_id)

        data = request.POST.copy()
        data["gene"] = primer.gene

        primer_form = Forms.PrimerForm(data)
        status_form = Forms.StatusLocationForm(request.POST)
        arrival_date_form = Forms.ArrivalDateForm(request.POST)

        # when update button is pressed, save updates made to current primer
        if request.POST.get("update_primer_button"):
            if (primer_form.is_valid() and 
                status_form.is_valid() and
                arrival_date_form.is_valid()
            ):
                logger_editing.info("Editing primer")
                logger_editing.info("Data stored:")

                for field, value in model_to_dict(primer).items():
                    logger_editing.info(" - {}: {}".format(field, value))

                logger_editing.info("Data submitted by scientist:")

                for field, value in request.POST.items():
                    if field != "csrfmiddlewaretoken" and "button" not in field:
                        logger_editing.info(" - {}: {}".format(field, value))

                # the form is valid
                primer_name = primer_form.cleaned_data["name"]
                gene = primer_form.cleaned_data["gene"] 
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
                logger_editing.info("Using status: {}".format(new_status))

                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                if created:
                    logger_editing.info("New scientist added to db: {}".format(new_scientist))
                else:
                    logger_editing.info("Scientist submitting primer: {}".format(new_scientist))

                new_pcr, created = Models.PCRProgram.objects.update_or_create(
                    name = pcr_program)

                if created:
                    logger_editing.info("New pcr program added to db: {}".format(new_pcr))
                else:
                    logger_editing.info("Using pcr program: {}".format(new_pcr))

                new_buffer, created = Models.Buffer.objects.update_or_create(name = buffer)

                if created:
                    logger_editing.info("New buffer added to db: {}".format(new_buffer))
                else:
                    logger_editing.info("Using buffer: {}".format(new_buffer))

                # if primer is present updates, if not creates new instance in database
                new_primer, created =  Models.PrimerDetails.objects.update_or_create(
                    name = primer_name, defaults={
                        'gene' : gene, 'comments':  comments, 'arrival_date': arrival_date,
                        'location': location, 'status': new_status, 
                        'scientist': new_scientist,'pcr_program': new_pcr, 
                        'buffer': new_buffer
                })

                logger_editing.info("Updating primer: {} {}".format(new_primer.id, new_primer))
                logger_editing.info(" - Primer gene: {}".format(new_primer.gene))
                logger_editing.info(" - Primer sequence: {}".format(new_primer.sequence))
                logger_editing.info(" - Primer gc %: {}".format(new_primer.gc_percent))
                logger_editing.info(" - Primer tm: {}".format(new_primer.tm))

                messages.success(request, 'Primer "{}" successfully updated'.format(new_primer),
                    extra_tags="alert-success")

            else:
                # view for form with populated data from selected primer if form is invalid
                messages.error(request, "One of the forms is invalid", extra_tags="alert-danger")

                primer = Models.PrimerDetails.objects.get(pk = PrimerDetails_id)

                context_dict["primer_form"] = primer_form
                context_dict["status_form"] = status_form
                context_dict["arrival_date_form"] = arrival_date_form
                context_dict["primer"] = primer

                return render(request, 'primer_db/edit_primer.html', context_dict)

        # when delete button is pressed, delete current primer
        elif request.POST.get("delete_primer_button"):
            messages.success(request, 'Primer "{}" successfully deleted'.format(primer),
                extra_tags="alert-success")

            logger_deleting.info("Deleting {}".format(primer))
            
            primer.delete()

            return  redirect('/primer_db/')
    
        elif request.POST.get("check_snp_primer_button"):
            primer.snp_status = 3
            primer.snp_date = timezone.now()
            primer.save()

            logger_editing.info("SNP checking: {}".format(primer))

            messages.success(
                request, 'SNP checked primer "{}"'.format(primer),
                extra_tags="alert-success"
            )

            return redirect('/primer_db/')

        elif request.POST.get("update_date_button"):
            primer.last_date_used = timezone.now()
            primer.save()

            logger_editing.info("Updating last date used: {}".format(primer))
            
            messages.success(
                request, 'Last date used for primer "{}" successfully updated'.format(primer),
                extra_tags="alert-success"
            )

    primer = Models.PrimerDetails.objects.get(pk = PrimerDetails_id)

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
    location_form = Forms.StatusLocationForm(initial = model_to_dict(primer))
    arrival_date_form = Forms.ArrivalDateForm(initial = model_to_dict(primer))
    status_form =  Forms.StatusLocationForm(initial = model_to_dict(primer))

    context_dict["primer_form"] = primer_form
    context_dict["location_form"] = location_form
    context_dict["arrival_date_form"] = arrival_date_form
    context_dict["status_form"] = status_form

    context_dict["primer"] = primer

    # complicated parsing to display snp info
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
        # trick to fool form2 validation
        data = request.POST.copy()
        data["form2-buffer"] = data["form1-buffer"]
        data["form2-pcr_program"] = data["form1-pcr_program"]
        data["form2-forename"] = data["form1-forename"]
        data["form2-surname"] = data["form1-surname"]

        # data sent for first primer
        primer_form1 = Forms.PrimerForm(request.POST, prefix ="form1")
        status_loc_form1 = Forms.StatusLocationForm(request.POST, prefix ="form1")
        arrival_date_form1 = Forms.ArrivalDateForm(request.POST, prefix ="form1")

        # data sent for second primer
        primer_form2 = Forms.PrimerForm(data, prefix ="form2")
        status_loc_form2 = Forms.StatusLocationForm(request.POST, prefix ="form2")
        arrival_date_form2 = Forms.ArrivalDateForm(request.POST, prefix ="form2")

        list_forms = [primer_form1, status_loc_form1, arrival_date_form1,
                      primer_form2, status_loc_form2, arrival_date_form2]

        # data for first primer
        context_dict["primer_form1"] = primer_form1
        context_dict["arrival_date_form1"] = arrival_date_form1
        context_dict["status_loc_form1"] = status_loc_form1

        # data for second primer
        context_dict["primer_form2"] = primer_form2
        context_dict["arrival_date_form2"] = arrival_date_form2
        context_dict["status_loc_form2"] = status_loc_form2

        # check selected primer id
        primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)[0]

        if primer.pairs_id:
            # if primer is from a pair and to be edited in pair form
            pair = Models.PrimerDetails.objects.filter(pairs_id = primer.pairs_id)

            if len(pair) == 2:
                primer1, primer2 = pair

            elif len(pair) > 2:
                logger_editing.error("This pair id {} is shared by 3 or more primers".format(primer.pairs_id))
                messages.add_message(request,
                    messages.ERROR,
                    "Please contact BioinformaticsTeamGeneticsLab@addenbrookes.nhs.uk as this issue can't be solved from the interface",
                    extra_tags="alert-danger")
                return redirect("/primer_db/")

            else:
                logger_editing.error("This pair id {} is present in only one primer".format(primer.pairs_id))
                messages.add_message(request,
                    messages.ERROR,
                    "Please contact BioinformaticsTeamGeneticsLab@addenbrookes.nhs.uk as an underlying issue has been detected",
                    extra_tags="alert-danger"
                )
                return redirect('edit_primer', PrimerDetails_id = primer.id)

            context_dict["primer2"] = primer2        
            context_dict["primer1"] = primer1

        fields = ["name", "gene", "buffer", "pcr_program", "arrival_date", "status", 
            "location", "comments", "forename", "surname"
        ]

        # when update button is pressed, save updates made to current primer
        if request.POST.get("update_primers_button"):
            if (primer_form1.is_valid() and 
                status_loc_form1.is_valid() and
                arrival_date_form1.is_valid() and
                
                primer_form2.is_valid() and 
                status_loc_form2.is_valid() and
                arrival_date_form2.is_valid()
            ):
                logger_editing.info("Editing primer pair")
                logger_editing.info("Data stored for primer1:")

                for field, value in model_to_dict(primer1).items():
                    logger_editing.info(" - {}: {}".format(field, value))

                logger_editing.info("Data stored for primer2:")

                for field, value in model_to_dict(primer2).items():
                    logger_editing.info(" - {}: {}".format(field, value))

                logger_editing.info("Data submitted by scientist:")

                for field, value in data.items():
                    if field != "csrfmiddlewaretoken" and "button" not in field:
                        logger_editing.info(" - {}: {}".format(field, value))

                forms1 = []
                forms2 =[]

                # loop for adding correct fields to forms
                for field in fields:
                    if field == "status" or field == "location":
                        forms1.append(status_loc_form1.cleaned_data[field])
                        forms2.append(status_loc_form2.cleaned_data[field])
                    elif field == "arrival_date":
                        forms1.append(arrival_date_form1.cleaned_data[field])
                        forms2.append(arrival_date_form2.cleaned_data[field])
                    else:
                        forms1.append(primer_form1.cleaned_data[field])
                        forms2.append(primer_form2.cleaned_data[field])  

                # unpack variables for first form and save to db
                (primer_name, gene, buffer, pcr_program, arrival_date, status, 
                 location, comments, forename, surname) = forms1

                logger_editing.info("Creating or using meta items relating to primer1:")

                new_status, created = Models.Status.objects.update_or_create(name = status)
                logger_editing.info(" - Using status: {}".format(new_status))

                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                if created:
                    logger_editing.info(" - New scientist added to db: {}".format(new_scientist))
                else:
                    logger_editing.info(" - Scientist who submitted primer: {}".format(new_scientist))

                new_pcr, created = Models.PCRProgram.objects.update_or_create(name = pcr_program)

                if created:
                    logger_editing.info(" - New pcr program added to db: {}".format(new_pcr))
                else:
                    logger_editing.info(" - Using pcr program: {}".format(new_pcr))

                new_buffer, created = Models.Buffer.objects.update_or_create(name = buffer)

                if created:
                    logger_editing.info(" - New buffer added to db: {}".format(new_buffer))
                else:
                    logger_editing.info(" - Using buffer: {}".format(new_buffer))

                new_primer, created =  Models.PrimerDetails.objects.update_or_create(
                    name = primer_name, defaults={
                        'gene' : gene, 'comments': comments, 'arrival_date': arrival_date,
                        'location': location, 'status': new_status, 'scientist': new_scientist,
                        'pcr_program': new_pcr, 'buffer': new_buffer
                    }
                )

                logger_editing.info("Updating: {} {}".format(new_primer.id, new_primer))
                logger_editing.info(" - Primer gene: {}".format(new_primer.gene))
                logger_editing.info(" - Primer sequence: {}".format(new_primer.sequence))
                logger_editing.info(" - Primer gc %: {}".format(new_primer.gc_percent))
                logger_editing.info(" - Primer tm: {}".format(new_primer.tm))

                #################################################################################

                # unpack variables for second form and save to db
                (primer_name, gene, buffer, pcr_program, arrival_date, status, 
                 location, comments, forename, surname) = forms2

                logger_editing.info("Creating or using meta items relating to primer2:")

                new_status, created = Models.Status.objects.update_or_create(name = status)
                logger_editing.info(" - Using status: {}".format(new_status))

                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                new_pcr, created = Models.PCRProgram.objects.update_or_create(name = pcr_program)

                new_buffer, created = Models.Buffer.objects.update_or_create(name = buffer)

                new_primer, created =  Models.PrimerDetails.objects.update_or_create(
                    name = primer_name, defaults={
                        'gene' : gene, 'comments': comments, 'arrival_date': arrival_date,
                        'location': location, 'status': new_status, 'scientist': new_scientist,
                        'pcr_program': new_pcr, 'buffer': new_buffer
                    }
                )

                logger_editing.info("Updating primer: {} {}".format(new_primer.id, new_primer))
                logger_editing.info(" - Primer gene: {}".format(new_primer.gene))
                logger_editing.info(" - Primer sequence: {}".format(new_primer.sequence))
                logger_editing.info(" - Primer gc %: {}".format(new_primer.gc_percent))
                logger_editing.info(" - Primer tm: {}".format(new_primer.tm))

                messages.success(request, 'Primer "{}" and "{}" successfully updated'.format(primer1, primer2),
                    extra_tags="alert-success")

                return render(request, 'primer_db/edit_pair.html', context_dict)

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

                return render(request, 'primer_db/edit_pair.html', context_dict)

        elif request.POST.get("check_snp_primer1_button") or request.POST.get("check_snp_primer2_button"):
            # value of button is the primer name allowing me to use it directly in the filtering after
            checked_primer1 = request.POST.get("check_snp_primer1_button", None)
            checked_primer2 = request.POST.get("check_snp_primer2_button", None)

            if checked_primer1:
                primer = Models.PrimerDetails.objects.filter(name = checked_primer1)
            elif checked_primer2:
                primer = Models.PrimerDetails.objects.filter(name = checked_primer2)

            messages.success(request, 'Primer "{}" successfully snp checked'.format(primer[0]),
                extra_tags="alert-success")

            logger_editing.info("SNP checking {}".format(primer[0]))

            primer.update(snp_status = 3)
            primer.update(snp_date = timezone.now())

        elif request.POST.get("update_date_button"):
            queryset_primer1 = Models.PrimerDetails.objects.get(pk = primer1.id)
            queryset_primer2 = Models.PrimerDetails.objects.get(pk = primer2.id)

            logger_editing.info("Updating last date used for {} and {}".format(queryset_primer1, queryset_primer2))

            queryset_primer1.last_date_used = timezone.now()
            queryset_primer2.last_date_used = timezone.now()
            queryset_primer1.save()
            queryset_primer2.save()
            
            messages.success(
                request, 'Last date used for primer "{}" and "{}" successfully updated'.format(
                    queryset_primer1, queryset_primer2
                ),
                extra_tags="alert-success")

        elif request.POST.get("delete_primer1_button") or request.POST.get("delete_pair_button") or request.POST.get("delete_primer2_button"):
            # 2 ways to delete stuff: one primer or the pair
            delete_primer1 = request.POST.get("delete_primer1_button", None)
            delete_primer2 = request.POST.get("delete_primer2_button", None)
            delete_pair = request.POST.get("delete_pair_button", None)

            if delete_pair:
                pair_to_delete = primer1.pairs

                messages.success(request, 'Pair with "{}" "{}" successfully deleted'.format(primer1, primer2),
                    extra_tags="alert-success")

                logger_deleting.info("Deleting {}".format(primer1))
                logger_deleting.info("Deleting {}".format(primer2))
                logger_deleting.info("Deleting pair id: {}".format(pair_to_delete.id))

                primer1.delete()
                primer2.delete()
                pair_to_delete.delete()

                return redirect("/primer_db/")

            if delete_primer1:
                primer = Models.PrimerDetails.objects.get(pk = delete_primer1)
            elif delete_primer2:
                primer = Models.PrimerDetails.objects.get(pk = delete_primer2)
            
            pair_to_delete = primer.pairs

            paired_primer = Models.PrimerDetails.objects.filter(pairs__id = pair_to_delete.id).exclude(name = primer.name)[0]
            paired_primer.pairs_id = None
            paired_primer.save()

            messages.success(request, 'Primer "{}" successfully deleted'.format(primer),
                extra_tags="alert-success")

            logger_deleting.info("Deleting {}".format(primer))
            logger_deleting.info("Deleting pair id: {}".format(pair_to_delete.id))
            logger_deleting.info("Primer {} left without pair".format(paired_primer))
            
            pair_to_delete.delete()
            primer.delete()

            return  redirect('/primer_db/')

    # check selected primer id
    primer = Models.PrimerDetails.objects.filter(pk = PrimerDetails_id)[0]

    if primer.pairs_id:
        # if primer is from a pair and to be edited in pair form
        pair = Models.PrimerDetails.objects.filter(pairs_id = primer.pairs_id)

        if len(pair) == 2:
            primer1, primer2 = pair

        elif len(pair) > 2:
            logger_editing.error("This pair id {} is shared by 3 or more primers".format(primer.pairs_id))
            messages.error(request,
                "Please contact BioinformaticsTeamGeneticsLab@addenbrookes.nhs.uk as this issue can't be solved from the interface",
                extra_tags="alert-danger")
            return redirect("/primer_db/")
        else:
            logger_editing.error("This pair id {} is present in only one primer".format(primer.pairs_id))
            messages.error(request,
                "Please contact BioinformaticsTeamGeneticsLab@addenbrookes.nhs.uk as an underlying issue has been detected",
                extra_tags="alert-danger"
            )
            return redirect('edit_primer', PrimerDetails_id = primer.id)

        context_dict["primer2"] = primer2        
        context_dict["primer1"] = primer1
    
    else:
        return redirect('edit_primer', PrimerDetails_id = primer.id)

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
    arrival_date_form1 = Forms.ArrivalDateForm(initial = model_to_dict(primer1), prefix = "form1")
    status_loc_form1 = Forms.StatusLocationForm(initial = model_to_dict(primer1), prefix = "form1")

    # data for second primer
    primer_form2 = Forms.PrimerForm(initial = primer2_details_dict, prefix = "form2")
    arrival_date_form2 = Forms.ArrivalDateForm(initial = model_to_dict(primer2), prefix = "form2")
    status_loc_form2 = Forms.StatusLocationForm(initial = model_to_dict(primer2), prefix = "form2")

    # data for first primer
    context_dict["primer_form1"] = primer_form1
    context_dict["arrival_date_form1"] = arrival_date_form1
    context_dict["status_loc_form1"] = status_loc_form1

    # data for second primer
    context_dict["primer_form2"] = primer_form2
    context_dict["arrival_date_form2"] = arrival_date_form2
    context_dict["status_loc_form2"] = status_loc_form2

    context_dict["primer1"] = primer1

    # parsing for displaying snp info 
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