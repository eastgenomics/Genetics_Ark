# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render, redirect
from django.http import HttpResponse, FileResponse
from django.template import loader
from django.contrib import messages
from .tables import PrimerDetailsTable
from django_tables2 import RequestConfig
from django.forms.models import model_to_dict
from django.db.models import Q
from django.utils import timezone

from collections import defaultdict
import subprocess
import sys
import logging

import primer_db.forms as Forms
import primer_db.models as Models

# path to mapping script
sys.path.insert(1, '/mnt/storage/home/rainfoj/Projects/primer_mapper/bin/') 
import primer_mapper

sys.path.insert(1, '/mnt/storage/home/kimy/projects/primer_database/genetics_ark_django/utils/') 
import gnomAD_queries
import snp_check
import get_primer_vis
import smalt_mapping


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


def get_data_for_primer_vis(primer1, primer2):
    """ Get data for primer visualization """

    gene = primer1.gene
    start1_37, end1_37 = primer1.coordinates.start_coordinate_37, primer1.coordinates.end_coordinate_37
    start2_37, end2_37 = primer2.coordinates.start_coordinate_37, primer2.coordinates.end_coordinate_37
    start1_38, end1_38 = primer1.coordinates.start_coordinate_38, primer1.coordinates.end_coordinate_38
    start2_38, end2_38 = primer2.coordinates.start_coordinate_38, primer2.coordinates.end_coordinate_38

    ref2seq = {}
    starts = {}

    gene_data_path = "/mnt/storage/home/rainfoj/Projects/primer_mapper/data/"
    gene_data = defaultdict(lambda: defaultdict(tuple))

    for ref in ["37", "38"]:
        with open("{}/{}_genes_coords.txt".format(gene_data_path, ref)) as f:
            for line in f:
                gene_info = line.strip().split("\t")
                gene_symbol, chrom, start, end = [ele.strip() for ele in gene_info]

                if gene == gene_symbol:
                    if ref == "37":
                        start = min(start1_37, end1_37, start2_37, end2_37)
                        end = max(start1_37, end1_37, start2_37, end2_37)
                    elif ref == "38":
                        start = min(start1_38, end1_38, start2_38, end2_38)
                        end = max(start1_38, end1_38, start2_38, end2_38)

                    gene_data[ref][gene] = (chrom, start, end)
    
        if not gene_data:
            rescued_gene = snp_check.rescue_gene_symbol_with_HGNC(gene)

            if rescued_gene:
                with open("{}/{}_genes_coords.txt".format(gene_data_path, ref)) as f:
                    for line in f:
                        gene_info = line.strip().split("\t")
                        gene_symbol, chrom, start, end = [ele.strip() for ele in gene_info]

                        if gene == gene_symbol:
                            if ref == "37":
                                start = min(start1_37, end1_37, start2_37, end2_37)
                                end = max(start1_37, end1_37, start2_37, end2_37)
                            elif ref == "38":
                                start = min(start1_38, end1_38, start2_38, end2_38)
                                end = max(start1_38, end1_38, start2_38, end2_38)

                            gene_data[ref][gene] = (chrom, start, end)

        ref_file = "/mnt/storage/data/refs/homo_sapiens/GRCh{}/Homo_sapiens_assembly{}.fasta".format(ref, ref)

        chrom, start, end = gene_data[ref][gene]

        cmd = ["samtools", "faidx", ref_file, "{}:{}-{}".format(chrom.strip("chr"), start-80, end+80)]

        starts[ref] = start-80

        samtools_output = subprocess.run(cmd, stdout = subprocess.PIPE).stdout.decode("ascii")
        samtools_output = ''.join(samtools_output.splitlines(True)[1:])
        samtools_output = samtools_output.replace('\n', '')

        ref2seq[ref] = samtools_output

    return ref2seq, starts

        
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

    # function for filtering primers that have coverage for the given variant position  
    if request.method == 'POST':
        # list of id for the primers checked in the main table
        pks = request.POST.getlist('check')

        filter_form = Forms.FilterForm(request.POST)

        if filter_form.is_valid():
            clean_data = filter_form.cleaned_data
            filter_params = {}
            
            for field, value in clean_data.items():
                if value:
                    if field == "chrom":
                        filter_params["coordinates__chrom_no"] = value
                    elif field == "gene":
                        filter_params["gene__exact"] = value
                    elif field == "status":
                        filter_params["status__name"] = value
                    elif field == "name":
                        filter_params["name__icontains"] = value
                    elif field == "location":
                        filter_params["location__icontains"] = value
                    elif field == "position":
                        # special case: when filtering by genomic position, you want to get position between a pair of primers
                        # in addition to the position within the primers
                        # --> need to handle pairs and solo primers differently
                        bugged_primers = []
                        paired_primers = Models.PrimerDetails.objects.filter(pairs_id__isnull = False)
                        lonely_primers = Models.PrimerDetails.objects.filter(pairs_id__isnull = True)

                        if lonely_primers:
                            filtered_lonely_primers = lonely_primers.filter(
                                Q(
                                    coordinates__start_coordinate_37__gte = value,
                                    coordinates__end_coordinate_37__lte = value
                                ) | 
                                Q(
                                    coordinates__start_coordinate_38__gte = value,
                                    coordinates__end_coordinate_38__lte = value
                                )
                            )

                        if paired_primers:
                            primer_ids = []

                            for primer in paired_primers:
                                nb_in_pairs = len(paired_primers.filter(pairs_id = primer.pairs_id))
                                
                                if nb_in_pairs != 2:
                                    # there has been instances where a pair is more than 2 primers
                                    # checking and recording those instances
                                    bugged_primers.append((primer.id, primer.name, primer.pairs_id))
                                    continue

                                elif nb_in_pairs == 2:
                                    primer1, primer2 = paired_primers.filter(pairs_id = primer.pairs_id)

                                    coordinates_37 = [
                                        primer1.coordinates.start_coordinate_37, primer1.coordinates.end_coordinate_37,
                                        primer2.coordinates.start_coordinate_37, primer2.coordinates.end_coordinate_37
                                    ]
                                    coordinates_38 = [
                                        primer1.coordinates.start_coordinate_38, primer1.coordinates.end_coordinate_38,
                                        primer2.coordinates.start_coordinate_38, primer2.coordinates.end_coordinate_38
                                    ]

                                    if (min(coordinates_37) <= value <= max(coordinates_37) or
                                        min(coordinates_38) <= value <= max(coordinates_38)
                                    ):
                                        primer_ids.append(primer1.id)
                                        primer_ids.append(primer2.id)
                                                
                            filtered_paired_primers = paired_primers.filter(pk__in = primer_ids)

                            if bugged_primers:
                                logger_index.error("There are pair ids that are bugged")

                                for id_, primer, pairs_id in bugged_primers:
                                    logger_index.error(" - {} {} --> {}".format(id_, primer, pairs_id))

                                messages.add_message(request,
                                    messages.ERROR,
                                    "Please contact BioinformaticsTeamGeneticsLab@addenbrookes.nhs.uk as the filtering skipped {} primers".format(len(bugged_primers)),
                                    extra_tags="alert-danger"
                                )

                        filtered_position_primers = filtered_lonely_primers | filtered_paired_primers

            # need to use locals because an empty queryset can be the sign of:
            # - no results after filtering by position
            # - no position typed to filter by
            if "filtered_position_primers" in locals():
                primers = filtered_position_primers.filter(**filter_params)
            else:
                primers = Models.PrimerDetails.objects.filter(**filter_params)

            request.session['filtered'] = [primer.id for primer in primers]

            if any(clean_data.values()):
                context_dict["filter_params"] = clean_data

            table = PrimerDetailsTable(primers)

        else:
            messages.add_message(
                request,
                messages.ERROR,
                filter_form.errors["__all__"],
                extra_tags='alert-danger'
            )

            primers = Models.PrimerDetails.objects.all()
            table = PrimerDetailsTable(primers)

        # recalc button clicked in index
        if 'recalc' in request.POST:
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

            recalc_msg.append("Selected primers: <b>{}</b> and <b>{}</b>".format(primer1, primer2))

            if primer1.coordinates.strand == "+" and primer2.coordinates.strand == "-":
                f_start37 = primer1.coordinates.start_coordinate_37
                r_end37 = primer2.coordinates.end_coordinate_37
                f_start38 = primer1.coordinates.start_coordinate_38
                r_end38 = primer2.coordinates.end_coordinate_38

                coverage37 = "{}:{}-{}".format(primer1.coordinates.chrom_no, f_start37, r_end37)
                coverage38 = "{}:{}-{}".format(primer1.coordinates.chrom_no, f_start38, r_end38)

                recalc_msg.append("<b>{}</b> is forward and <b>{}</b> is reverse".format(primer1, primer2))

            elif primer2.coordinates.strand == "+" and primer1.coordinates.strand == "-":
                f_start37 = primer2.coordinates.start_coordinate_37
                r_end37 = primer1.coordinates.end_coordinate_37
                f_start38 = primer2.coordinates.start_coordinate_38
                r_end38 = primer1.coordinates.end_coordinate_38

                coverage37 = "{}:{}-{}".format(primer1.coordinates.chrom_no, f_start37, r_end37)
                coverage38 = "{}:{}-{}".format(primer1.coordinates.chrom_no, f_start38, r_end38)

                recalc_msg.append("<b>{}</b> is forward and <b>{}</b> is reverse".format(primer2, primer1))

            else:
                msg = "You need a forward and a reverse primer"
                messages.error(request, msg, extra_tags='alert-danger')
                return redirect('/primer_db/')

            amplicon_length_37 = r_end37 - f_start37
            amplicon_length_38 = r_end38 - f_start38

            recalc_msg.append("Recalculated coverage for GRCh37 is: <b>{}</b>".format(coverage37))
            recalc_msg.append("Recalculated coverage for GRCh38 is: <b>{}</b>".format(coverage38))

            if amplicon_length_37 < 0:
                recalc_msg.append("Amplification not possible in GRCh37 with this pair of primer")
            if amplicon_length_38 < 0:
                recalc_msg.append("Amplification not possible in GRCh38 with this pair of primer")

            recalc_msg.append("Amplicon length in GRCh37 is: <b>{}</b>".format(amplicon_length_37))
            recalc_msg.append("Amplicon length in GRCh38 is: <b>{}</b>".format(amplicon_length_38))

            logger_index.info("Recalculating for {} and {}".format(primer1, primer2))

            primers = Models.PrimerDetails.objects.all()
            table = PrimerDetailsTable(primers)
            context_dict["recalc"] = recalc_msg

        elif 'change_status' in request.POST:
            new_status = request.POST.get('new_status') # get status to change to from POST data
            update_status = Models.Status.objects.get(name=new_status)

            for pk in pks:
                primer = Models.PrimerDetails.objects.get(pk=pk)
                primer.status = update_status
                primer.save()

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    "Updating {} status to {}".format(primer, update_status),
                    extra_tags='alert-success'
                )

                logger_index.info("CHANGING STATUS OF \"{}\" TO \"{}\"".format(primer, update_status))

            filtered_primers = request.session.get('filtered', None)

            if filtered_primers:
                primers = Models.PrimerDetails.objects.filter(pk__in = filtered_primers)
            else:
                primers = Models.PrimerDetails.objects.all()
            
            table = PrimerDetailsTable(primers)

        elif 'failed_snp_check' in request.POST or "manually_snp_check" in request.POST or "not_recognized_snp_check" in request.POST:
            if "failed_snp_check" in request.POST:
                status = "2"
            elif "manually_snp_check" in request.POST:
                status = "3"
            elif "not_recognized_snp_check" in request.POST:
                status = "4"

            filtered_primers = request.session.get("filtered", None)

            if filtered_primers:               
                primers = Models.PrimerDetails.objects.filter(pk__in=filtered_primers, snp_status=status)
            else:
                primers = Models.PrimerDetails.objects.filter(snp_status = status)

            primer_ids = [primer.id for primer in primers]

            request.session["primer_ids_snp"] = primer_ids

            table = PrimerDetailsTable(primers)

    else:
        filtered_primers = request.session.get("filtered", None)
        filtered_snps = request.session.get("primer_ids_snp", None)

        if filtered_snps and "page" in request.GET:
            primers = Models.PrimerDetails.objects.filter(pk__in = filtered_snps)

        elif filtered_primers and "page" in request.GET:
            primers = Models.PrimerDetails.objects.filter(pk__in = filtered_primers)

        else:
            primers = Models.PrimerDetails.objects.all()

            if filtered_snps:
                del request.session["primer_ids_snp"]

            if filtered_primers:
                del request.session["filtered"]

        table = PrimerDetailsTable(primers)

    context_dict["filter_form"] = Forms.FilterForm()

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

    context_dict = {}
    logging_dict = defaultdict(lambda: defaultdict())

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

        logger_submit.info("SUBMITING SINGLE PRIMER...")

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

                # save primer to database
                status_object = Models.Status.objects.filter(name = status)[0]

                new_scientist, created = Models.Scientist.objects.get_or_create(
                    forename = forename, surname = surname)

                logging_dict["scientist"]["created"] = created
                logging_dict["scientist"]["object"] = new_scientist

                new_pcr, created = Models.PCRProgram.objects.get_or_create(
                    name = pcr_program)

                logging_dict["pcr_program"]["created"] = created
                logging_dict["pcr_program"]["object"] = new_pcr

                new_buffer, created = Models.Buffer.objects.get_or_create(name = buffer)

                logging_dict["buffer"]["created"] = created
                logging_dict["buffer"]["object"] = new_buffer

                new_coordinates, created = Models.Coordinates.objects.get_or_create(
                    start_coordinate_37 = start_coordinate_37, end_coordinate_37 = end_coordinate_37,
                    start_coordinate_38 = start_coordinate_38, end_coordinate_38 = end_coordinate_38, 
                    chrom_no = gene_chrom, strand = strand
                )

                logging_dict["coordinates"]["created"] = created
                logging_dict["coordinates"]["object"] = new_coordinates

                new_primer = Models.PrimerDetails.objects.create(
                    name = name, gene = gene, sequence = sequence, 
                    gc_percent = gc_percent, tm = tm,
                    comments =  comments, arrival_date = arrival_date,
                    location = location, snp_status = snp_status,
                    snp_date = snp_date, snp_info = ";".join(snp_info),
                    status = status_object, scientist = new_scientist, 
                    pcr_program = new_pcr, buffer = new_buffer, 
                    coordinates = new_coordinates
                )

                logger_submit.info("Created primer: {} {}".format(new_primer.id, new_primer))
                logger_submit.info(" - Primer gene: {}".format(new_primer.gene))
                logger_submit.info(" - Primer sequence: {}".format(new_primer.sequence))
                logger_submit.info(" - Primer gc %: {}".format(new_primer.gc_percent))
                logger_submit.info(" - Primer tm: {}".format(new_primer.tm))

                if snp_info:
                    logger_submit.info(" - Detected snps in primer")
                else:
                    logger_submit.info(" - No snps detected")

                logger_submit.info(" - Using status: {}".format(status_object))

                for field, data in logging_dict.items():
                    if data["created"]:
                        logger_submit.info(" - New {} created: {}".format(field, data["object"]))
                    else:
                        logger_submit.info(" - Using {}: {}".format(field, data["object"]))

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

        logger_submit.info("SUBMITTING PRIMER PAIR...")

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

                if isinstance(mapping_37, str):
                    messages.error(request, "{}".format(mapping_37), extra_tags= "alert-danger")
                    return render(request, "primer_db/submit_pair.html", context_dict)

                if isinstance(mapping_38, str):
                    messages.error(request, "{}".format(mapping_38), extra_tags= "alert-danger")
                    return render(request, "primer_db/submit_pair.html", context_dict)

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
                    logging_common = defaultdict(lambda: defaultdict())
                    logger_submit.info("Common info for primers:")

                    amplicon_37 = coverage_37.split(":")[1].split("-")
                    amplicon_38 = coverage_37.split(":")[1].split("-")

                    new_pair = Models.Pairs.objects.create(
                        coverage_37 = coverage_37, coverage_38 = coverage_38,
                        size_37 = int(max(amplicon_37)) - int(min(amplicon_37)),
                        size_38 = int(max(amplicon_38)) - int(min(amplicon_38))
                    )

                    logging_common["pair"]["created"] = True
                    logging_common["pair"]["object"] = new_pair.id

                    new_scientist, created = Models.Scientist.objects.get_or_create(
                        forename = forename, surname = surname)

                    logging_common["scientist"]["created"] = created
                    logging_common["scientist"]["object"] = new_scientist

                    new_pcr, created = Models.PCRProgram.objects.get_or_create(
                        name = pcr_program)

                    logging_common["pcr_program"]["created"] = created
                    logging_common["pcr_program"]["object"] = new_pcr

                    new_buffer, created = Models.Buffer.objects.get_or_create(name = buffer)

                    logging_common["buffer"]["created"] = created
                    logging_common["buffer"]["object"] = new_buffer

                    for field, data in logging_common.items():
                        if data["created"]:
                            logger_submit.info(" - New {} created : {}".format(field, data["object"]))
                        else:
                            logger_submit.info(" - Using {} : {}".format(field, data["object"]))

                    #############################################################

                    logging_primer1 = defaultdict(lambda: defaultdict())

                    snp_status1, snp_date1, snp_info1 = snp_check.main(
                        gene, primer1_start_37, primer1_end_37,
                        primer1_start_38, primer1_end_38
                    )

                    new_status1, created = Models.Status.objects.get_or_create(name = status1)

                    logging_primer1["status"]["created"] = created
                    logging_primer1["status"]["object"] = new_status1

                    new_coordinates1, created = Models.Coordinates.objects.get_or_create(
                        start_coordinate_37 = primer1_start_37, end_coordinate_37 = primer1_end_37,
                        start_coordinate_38 = primer1_start_38, end_coordinate_38 = primer1_end_38,
                        chrom_no = gene_chrom, strand = primer1_strand
                        )

                    logging_primer1["status"]["created"] = created
                    logging_primer1["status"]["object"] = new_coordinates1

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
                    
                    if snp_info1:
                        logger_submit.info(" - SNPs detected in primer")
                    else:
                        logger_submit.info(" - No SNPs detected in primer")
                    
                    for field, data in logging_primer1.items():
                        if data["created"]:
                            logger_submit.info(" - New {} created: {}".format(field, data["object"]))
                        else:
                            logger_submit.info(" - Using {}: {}".format(field, data["object"]))

                    #############################################################

                    logging_primer2 = defaultdict(lambda: defaultdict())

                    snp_status2, snp_date2, snp_info2 = snp_check.main(
                        gene, primer2_start_37, primer2_end_37,
                        primer2_start_38, primer2_end_38
                    )

                    # save primer 2 to database
                    new_status2, created = Models.Status.objects.get_or_create(name = status2)

                    logging_primer2["status"]["created"] = created
                    logging_primer2["status"]["object"] = new_status2

                    new_coordinates2, created = Models.Coordinates.objects.get_or_create(
                        start_coordinate_37 = primer2_start_37, end_coordinate_37 = primer2_end_37,
                        start_coordinate_38 = primer2_start_38, end_coordinate_38 = primer2_end_38,
                        chrom_no = gene_chrom, strand = primer2_strand
                    )

                    logging_primer2["coordinates"]["created"] = created
                    logging_primer2["coordinates"]["object"] = new_coordinates2

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

                    if snp_info2:
                        logger_submit.info(" - SNPs detected in primer")
                    else:
                        logger_submit.info(" - No SNPs detected in primer")
                    
                    for field, data in logging_primer2.items():
                        if data["created"]:
                            logger_submit.info(" - New {} created: {}".format(field, data["object"]))
                        else:
                            logger_submit.info(" - Using {}: {}".format(field, data["object"]))

                    # success save message passed to submit.html
                    messages.success(request, 'Primers {} and {} successfully saved'.format(new_primer1, new_primer2),
                        extra_tags="alert-success")

                    multiple_mapping_res = smalt_mapping.multiple_mapping_check(new_primer1, new_primer2)

                    if not multiple_mapping_res:
                        messages.warning(request, "Multiple mapping check failed", extra_tags="alert-warning")

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

        list_forms = [primer_form, arrival_date_form, status_form]

        # when update button is pressed, save updates made to current primer
        if request.POST.get("update_primer_button"):
            if (primer_form.is_valid() and 
                status_form.is_valid() and
                arrival_date_form.is_valid()
            ):
                logging_dict = defaultdict(lambda: defaultdict())
                logger_editing.info("EDITING SINGLE PRIMER...")
                logger_editing.info("Data stored:")

                for field, value in model_to_dict(primer).items():
                    logger_editing.info(" - {}: {}".format(field, value))

                logger_editing.info("Data submitted by scientist:")

                for field, value in request.POST.items():
                    if field != "csrfmiddlewaretoken" and "button" not in field:
                        logger_editing.info(" - {}: {}".format(field, value))

                # the form is valid
                new_primer_name = primer_form.cleaned_data["name"]
                status = status_form.cleaned_data["status"]
                new_comments = primer_form.cleaned_data["comments"]
                new_arrival_date = arrival_date_form.cleaned_data["arrival_date"]
                buffer = primer_form.cleaned_data["buffer"].capitalize()
                pcr_program = primer_form.cleaned_data["pcr_program"]
                forename = primer_form.cleaned_data["forename"].capitalize()
                surname = primer_form.cleaned_data["surname"].capitalize()
                location = status_form.cleaned_data["location"]

                # save primer to database
                new_status, created = Models.Status.objects.update_or_create(name = status)

                logging_dict["status"]["created"] = created
                logging_dict["status"]["object"] = new_status

                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                logging_dict["scientist"]["created"] = created
                logging_dict["scientist"]["object"] = new_scientist

                new_pcr, created = Models.PCRProgram.objects.update_or_create(
                    name = pcr_program)

                logging_dict["pcr_program"]["created"] = created
                logging_dict["pcr_program"]["object"] = new_pcr

                new_buffer, created = Models.Buffer.objects.update_or_create(name = buffer)

                logging_dict["buffer"]["created"] = created
                logging_dict["buffer"]["object"] = new_buffer

                # params dict to update the relevant fields
                update_params = {}

                if new_primer_name != primer.name:
                    update_params["name"] = new_primer_name
                if new_comments != primer.comments:
                    update_params["comments"] = new_comments
                if new_arrival_date != primer.arrival_date:
                    update_params["arrival_date"] = new_arrival_date

                for field, data in logging_dict.items():
                    if data["object"] != model_to_dict(primer)[field]:
                        update_params[field] = data["object"]
                
                # if primer is present updates, if not creates new instance in database
                new_primer = Models.PrimerDetails.objects.filter(id=primer.id).update(**update_params)

                logger_editing.info("Updating primer: {} {}".format(primer.id, primer))

                for field, data in logging_dict.items():
                    if data["created"]:
                        logger_editing.info(" - New {} created: {}".format(field, data["object"]))
                    else:
                        logger_editing.info(" - Using {}: {}".format(field, data["object"]))                

                messages.success(request, 'Primer "{}" successfully updated'.format(primer),
                    extra_tags="alert-success")

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

        # when delete button is pressed, delete current primer
        elif request.POST.get("delete_primer_button"):
            messages.success(request, 'Primer "{}" successfully deleted'.format(primer),
                extra_tags="alert-success")

            logger_deleting.info("DELETING: {}".format(primer))
            
            primer.delete()

            return  redirect('/primer_db/')
    
        elif request.POST.get("check_snp_primer_button"):
            primer.snp_status = 3
            primer.snp_date = timezone.now()
            primer.save()

            logger_editing.info("SNP CHECKING: {}".format(primer))

            messages.success(
                request, 'Checked SNPS of "{}"'.format(primer),
                extra_tags="alert-success"
            )

            return redirect('/primer_db/')

        elif request.POST.get("update_date_button"):
            primer.last_date_used = timezone.now()
            primer.save()

            logger_editing.info("UPDATING LAST DATE USED: {}".format(primer))
            
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
        # check selected primer id
        primer = Models.PrimerDetails.objects.get(pk = PrimerDetails_id)

        if primer.pairs_id:
            # if primer is from a pair and to be edited in pair form
            paired_primers = Models.PrimerDetails.objects.filter(pairs_id = primer.pairs_id)

            if len(paired_primers) == 2:
                primer1, primer2 = paired_primers

            elif len(paired_primers) > 2:
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

        # trick to fool form2 validation
        data = request.POST.copy()
        data["form1-gene"] = primer1.gene
        data["form2-gene"] = primer2.gene
        data["form2-buffer"] = data["form1-buffer"]
        data["form2-pcr_program"] = data["form1-pcr_program"]
        data["form2-forename"] = data["form1-forename"]
        data["form2-surname"] = data["form1-surname"]

        # data sent for first primer
        primer_form1 = Forms.PrimerForm(data, prefix ="form1")
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

        fields = [
            "name", "gene", "buffer", "pcr_program", "arrival_date",
            "status", "location", "comments", "forename", "surname"
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
                logger_editing.info("EDITING PRIMER PAIR...")
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
                logging_dict = defaultdict(lambda: defaultdict())

                (new_primer_name, gene, buffer, pcr_program, new_arrival_date, status, 
                 location, new_comments, forename, surname) = forms1

                logger_editing.info("Creating or using meta items relating to both primers:")

                new_status, created = Models.Status.objects.update_or_create(name = status)

                logging_dict["status"]["created"] = created
                logging_dict["status"]["object"] = new_status

                new_scientist, created = Models.Scientist.objects.update_or_create(
                    forename = forename, surname = surname)

                logging_dict["scientist"]["created"] = created
                logging_dict["scientist"]["object"] = new_scientist

                new_pcr, created = Models.PCRProgram.objects.update_or_create(name = pcr_program)

                logging_dict["pcr_program"]["created"] = created
                logging_dict["pcr_program"]["object"] = new_pcr

                new_buffer, created = Models.Buffer.objects.update_or_create(name = buffer)

                logging_dict["buffer"]["created"] = created
                logging_dict["buffer"]["object"] = new_buffer

                for field, data in logging_dict.items():
                    if data["created"]:
                        logger_editing.info(" - New {} created: {}".format(field, data["object"]))
                    else:
                        logger_editing.info(" - Using {}: {}".format(field, data["object"]))

                #################################################################################

                # params dict to update the relevant fields
                update_params = {}

                if new_primer_name != primer1.name:
                    update_params["name"] = new_primer_name
                if new_comments != primer1.comments:
                    update_params["comments"] = new_comments
                if new_arrival_date != primer1.arrival_date:
                    update_params["arrival_date"] = new_arrival_date

                for field, data in logging_dict.items():
                    if data["object"] != model_to_dict(primer)[field]:
                        update_params[field] = data["object"]

                Models.PrimerDetails.objects.filter(id=primer1.id).update(**update_params)

                logger_editing.info("Updating: {} {}".format(primer1.id, primer1))

                #################################################################################

                # unpack variables for second form and save to db
                (new_primer_name, gene, buffer, pcr_program, new_arrival_date, status, 
                 location, new_comments, forename, surname) = forms2

                # params dict to update the relevant fields
                update_params = {}

                if new_primer_name != primer2.name:
                    update_params["name"] = new_primer_name
                if new_comments != primer2.comments:
                    update_params["comments"] = new_comments
                if new_arrival_date != primer2.arrival_date:
                    update_params["arrival_date"] = new_arrival_date

                for field, data in logging_dict.items():
                    if data["object"] != model_to_dict(primer)[field]:
                        update_params[field] = data["object"]

                Models.PrimerDetails.objects.filter(id=primer2.id).update(**update_params)

                logger_editing.info("Updating primer: {} {}".format(primer2.id, primer2))

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

        elif request.POST.get("check_snp_primer1_button") or request.POST.get("check_snp_primer2_button"):
            # value of button is the primer name allowing me to use it directly in the filtering after
            checked_primer1 = request.POST.get("check_snp_primer1_button", None)
            checked_primer2 = request.POST.get("check_snp_primer2_button", None)

            if checked_primer1:
                primer = Models.PrimerDetails.objects.get(name = checked_primer1)
            elif checked_primer2:
                primer = Models.PrimerDetails.objects.get(name = checked_primer2)

            messages.success(request, 'Primer "{}" successfully snp checked'.format(primer),
                extra_tags="alert-success")

            logger_editing.info("SNP CHECKING {}".format(primer))

            primer.update(snp_status = 3)
            primer.update(snp_date = timezone.now())

        elif request.POST.get("update_date_button"):
            queryset_primer1 = Models.PrimerDetails.objects.get(pk = primer1.id)
            queryset_primer2 = Models.PrimerDetails.objects.get(pk = primer2.id)

            logger_editing.info("UPDATATING LAST DATE USED FOR \"{}\" AND \"{}\"".format(queryset_primer1, queryset_primer2))

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

                logger_deleting.info("DELETING: {}".format(primer1))
                logger_deleting.info("DELETING: {}".format(primer2))
                logger_deleting.info("DELETING PAIR ID: {}".format(pair_to_delete.id))

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

            logger_deleting.info("DELETING: {}".format(primer))
            logger_deleting.info("DELETING PAIR ID: {}".format(pair_to_delete.id))
            logger_deleting.info("{} LEFT WITHOUT PAIR".format(paired_primer))
            
            pair_to_delete.delete()
            primer.delete()

            return  redirect('/primer_db/')

        elif request.POST.get("visualization_button"):
            vis_path_37 = "primer_db/primer_visualization/{}-{}_37.pdf".format(primer1, primer2)
            vis_path_38 = "primer_db/primer_visualization/{}-{}_38.pdf".format(primer1, primer2)

            ref2seq, starts = get_data_for_primer_vis(primer1, primer2)
            primers = get_primer_vis.get_data_from_django(primer1, primer2)
            created = get_primer_vis.main(starts, ref2seq, primers)

            if created:
                logger_editing.info("CREATED: {}".format(vis_path_37))
                logger_editing.info("CREATED: {}".format(vis_path_38))
            else:
                logger_editing.info("ALREADY EXISTS, OPENING: {}".format(vis_path_37))
                logger_editing.info("ALREADY EXISTS, OPENING: {}".format(vis_path_38))

            if request.POST.get("visualization_button") == "37":
                return FileResponse(
                    open(vis_path_37, 'rb'),
                    content_type='application/pdf'
                )
            elif request.POST.get("visualization_button") == "38":
                return FileResponse(
                    open(vis_path_38, 'rb'),
                    content_type='application/pdf'
                )

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