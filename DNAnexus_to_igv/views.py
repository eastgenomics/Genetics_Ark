# -*- coding: utf-8 -*-

"""
Django app to link Genetics Ark to samples in DNAnexus cloud platform.

A sample ID is taken as input through a search field, this is queried
against DNAnexus for BAMs in 002 sequencing projects. If BAM(s) are
found, pre authenticated dx download links for the BAM(s) and their
respective index files are generated. These are returned to the page,
along with a button to open IGV.js through Genetics Ark, passing the
generated links to directly stream and view the BAMs.

The dx-toolkit environment must first be sourced and user logged in.
dx_002_bams.json must also be present in DNAnexus_to_igv/, this is
generated from find_dx_002_bams.py
"""
import json
import logging
from pathlib import Path
import re
import ast

from django.contrib import messages
# from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django.shortcuts import render
import dxpy as dx

from DNAnexus_to_igv.forms import UrlForm, SearchForm

from ga_core.settings import (
    FASTA_37, FASTA_IDX_37, CYTOBAND_37, REFSEQ_37,
    FASTA_38, FASTA_IDX_38, CYTOBAND_38, REFSEQ_38,
    DNANEXUS_TOKEN, SLACK_TOKEN, DEBUG
)
from .find_dx_data import dx_login

logger = logging.getLogger("general")


def get_dx_urls(sample_id, bam_file_id, bam_file_name, idx_file_id,
                idx_file_name, project_id):
    """
    Get preauthenticated dx download urls for file and its index

    Args:
        - sample-id (str): for error reporting purpose
        - bam_file_id (str): BAM/CNV file-id
        - idx_file_id (str): BAM/CNV index file-id
        - bam_file_name (str): BAM/CNV filename
        - idx_file_name (str): BAM/CNV index filename
        - project_id (str): project-id
    Returns:
        - bam_url (str): DNAnexus url for downloading BAM/CNV file
        - idx_url (str): DNAnexus url for downloading its index file
    """
    dx_login(DNANEXUS_TOKEN, SLACK_TOKEN, DEBUG)

    try:
        bam_info = dx.bindings.dxfile.DXFile(
            dxid=bam_file_id, project=project_id
        )
        bam = bam_info.get_download_url(
            duration=3600, preauthenticated=True,
            project=project_id, filename=bam_file_name
        )
        idx_info = dx.bindings.dxfile.DXFile(
            dxid=idx_file_id, project=project_id
        )
        idx = idx_info.get_download_url(
            duration=3600, preauthenticated=True,
            project=project_id, filename=idx_file_name
        )
        # returns tuple with url as first
        bam_url = bam[0]
        idx_url = idx[0]

    except Exception as e:
        logger.error(
            f'Error generating dx download url for sample '
            f'{sample_id} in {project_id}'
            )
        logger.error(e)

        bam_url = None
        idx_url = None

    return bam_url, idx_url


# @login_required
def nexus_search(request):
    """
    Main search page function.

    On searching:
    - a list of 002 project ids is generated from get_002_projects()
    - for each project, dx_find_bams() is used to search for BAMs
    - on finding matching BAM and index, urls are generated with
      get_dx_urls()
    - renders page with download urls and a button to load igv.js with links
    """

    context_dict = {}
    context_dict["search_form"] = SearchForm()
    context_dict["url_form"] = UrlForm()

    if request.method == 'POST':
        # WHEN SEARCH BUTTON IS PRESSED
        if request.POST['action'] == 'search':
            sample_id = request.POST["sample_id"]
            sample_id = str(sample_id).strip()  # in case spaces

            try:
                # load in json with all bams and dx attributes needed to
                # search and generate dx download links
                # if json is not present it will raise IOError
                json_path = Path(__file__).parent.absolute()
                json_file = f'{json_path}/jsons/dx_002_bams.json'
                logger.info(f'JSON FILE PATH: {json_file}')

                with open(json_file) as json_file:
                    json_bams = json.load(json_file)

            except IOError as IOe:
                messages.add_message(
                    request,
                    messages.ERROR,
                    """An error has occured connecting with\
                    DNAnexus to find samples, please contact\
                    the bioinformatics team"""
                )
                logger.error(IOe)

                return render(
                    request, 'DNAnexus_to_igv/nexus_search.html', context_dict)

            if request.POST['sample_type'] == 'BAM':
                # select bams matching sample id, return original entry from
                # JSON by matching against upper name and search term
                # (structure of json may be found in find_dx_bams.py)
                # change to search partial
                sample_data = [
                    value for key, value in json_bams['BAM'].items() if
                    sample_id.upper() in key.upper()]
            else:
                # CNV handling
                sample_data = [
                    value for key, value in json_bams['CNV'].items() if
                    key.upper() in sample_id.upper()]

            # NO BAM FOUND
            if len(sample_data) == 0:
                messages.add_message(
                    request,
                    messages.ERROR,
                    mark_safe(
                        """Sample {} is not found in DNAnexus, either it is\
                        not available, the sample name is incorrect\
                        or some other error. Please contact\
                        the Bioinformatics team if you believe the sample\
                        should be available.""".format(sample_id)),
                    extra_tags="alert-danger"
                )
                logger.error((re.sub(
                    r'\s+', ' ', """Sample {} not found in JSON. Either sample
                    name mistyped or an error in finding the BAMs for the
                    sample, possibly missing index.""".format(sample_id)
                )))

                return render(
                    request, 'DNAnexus_to_igv/nexus_search.html', context_dict)

            flat_data = [x for xs in sample_data for x in xs]

            logger.info(f'{len(flat_data)} sample found')

            if len(flat_data) == 1:
                # ONLY ONE SAMPLE FOUND
                sample_dict = flat_data[0]

                file_url, idx_url = get_dx_urls(
                    sample_id,
                    sample_dict["file_id"],
                    sample_dict["file_name"],
                    sample_dict["idx_id"],
                    sample_dict["idx_name"],
                    sample_dict["project_id"]
                )

                if file_url is None or idx_url is None:
                    # error generating urls, display message
                    messages.add_message(
                        request,
                        messages.ERROR,
                        mark_safe(
                            "Error generating download URLs for sample "
                            f"{sample_id}. Please contact the bioinformatics "
                            "team for help."), extra_tags="alert-danger"
                    )

                    logger.error(
                        f'Error generating url for sample {sample_id}.'
                        'Additional info: {sample_dict}'
                        )

                    return render(
                        request, 'DNAnexus_to_igv/nexus_search.html',
                        context_dict
                    )

                context_dict["file_url"] = file_url
                context_dict["idx_url"] = idx_url
                context_dict["sample_id"] = sample_id
                context_dict['file_id'] = sample_dict['file_id']
                context_dict["file_name"] = sample_dict["file_name"]
                context_dict["project_name"] = sample_dict["project_name"]
                context_dict['file_path'] = sample_dict['file_path']
                context_dict['file_archival_state'] = sample_dict[
                    'file_archival_state']
                context_dict['idx_archival_state'] = sample_dict[
                    'idx_archival_state']

                return render(
                    request, 'DNAnexus_to_igv/nexus_search.html', context_dict)
            else:
                # MULTIPLE BAMS FOUND

                context_dict["sample_id"] = sample_id

                bam_list = []

                for bam in flat_data:
                    # can be mix of lists and nested lists
                    if "dev" in bam["project_name"].lower():
                        # if dev data project add development after path
                        path = f"{bam['file_path']} - DEVELOPMENT"
                    else:
                        path = bam['file_path']

                    bam_list.append({
                        "file_name": bam["file_name"],
                        "idx_name": bam["idx_name"],
                        "project_name": bam["project_name"],
                        "project_id": bam["project_id"],
                        "file_path": path,
                        "idx_id": bam["idx_id"],
                        "file_id": bam["file_id"],
                        "file_archival_state": bam["file_archival_state"],
                        "idx_archival_state": bam["idx_archival_state"]
                    })

                context_dict["bam_list"] = bam_list
                context_dict["file_no"] = len(bam_list)

                return render(
                    request, 'DNAnexus_to_igv/nexus_search.html', context_dict)

        elif request.POST['action'] == 'select_bam':
            # IN MULTIPLE BAM LIST, WHEN ONE BAM IS SELECTED
            # BAM has been selected, save bam data before flushing session
            selected_file_id = request.POST['selected_file_id']
            session_bams = ast.literal_eval(request.POST['bam_list'])

            for bam in session_bams:
                if selected_file_id == bam['file_id']:
                    sample_id = request.POST['sample_id']

                    # generate urls for selected sample
                    file_url, idx_url = get_dx_urls(
                        sample_id,
                        bam["file_id"],
                        bam["file_name"],
                        bam["idx_id"],
                        bam["idx_name"],
                        bam["project_id"]
                    )

                    context_dict["sample_id"] = sample_id
                    context_dict["file_name"] = bam["file_name"]
                    context_dict["project_name"] = bam["project_name"]
                    context_dict["file_url"] = file_url
                    context_dict["idx_url"] = idx_url
                    context_dict['file_path'] = bam['file_path']
                    context_dict['file_id'] = bam['file_id']
                    context_dict['idx_id'] = bam['idx_id']
                    context_dict['file_archival_state'] = bam[
                        'file_archival_state']
                    context_dict['idx_archival_state'] = bam[
                        'idx_archival_state']

                    return render(
                        request,
                        'DNAnexus_to_igv/nexus_search.html',
                        context_dict)

        # WHEN DIRECT URL LINK SELECTED
        elif (request.POST['action'] == 'form_37'
                or request.POST['action'] == 'form_38'):

            form = UrlForm(request.POST)
            file_url = request.POST['file_url']
            idx_url = request.POST['index_url']

            if form.is_valid():
                pass
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    """An error has occured loading IGV from the\
                        provided URLs. Please check URLs are correct\
                        and have been pasted in the correct fields.
                        URLs used:
                        File: {file_url}
                        Index: {idx_url}""".format(
                        file_url=file_url, idx_url=idx_url
                    ), extra_tags="alert-danger"
                )

                logger.error(
                    "Error loading IGV from pasted urls, most likely pasted "
                    f"in wrong fields. BAM URL: {file_url}. Index URL: "
                    f"{idx_url}"
                )

                return render(
                    request, 'DNAnexus_to_igv/nexus_search.html', context_dict)

            # if "bai" not ifile and "bai" in idx_url:
            # check urls in correct fields
            context_dict["sample_id"] = "DIRECT URL"
            context_dict["file_url"] = file_url
            context_dict["idx_url"] = idx_url

            # check for reference by button name pressed
            if request.POST['action'] == 'url_37':
                context_dict["reference"] = "hg19"
                context_dict["fasta"] = FASTA_37
                context_dict["fasta_idx"] = FASTA_IDX_37
                context_dict["cytoband"] = CYTOBAND_37
                context_dict["refseq"] = REFSEQ_37
            else:
                context_dict["reference"] = "hg38"
                context_dict["fasta"] = FASTA_38
                context_dict["fasta_idx"] = FASTA_IDX_38
                context_dict["cytoband"] = CYTOBAND_38
                context_dict["refseq"] = REFSEQ_38

            return render(
                request, 'DNAnexus_to_igv/nexus_igv.html', context_dict)
        else:
            # WHEN VIEW IN IGV IS SELECTED (SINGLE SAMPLE VIEW)
            # check for reference by button name pressed
            if request.POST['action'] == 'igv_37':
                context_dict["reference"] = "hg19"
                context_dict["fasta"] = FASTA_37
                context_dict["fasta_idx"] = FASTA_IDX_37
                context_dict["cytoband"] = CYTOBAND_37
                context_dict["refseq"] = REFSEQ_37
            else:
                context_dict["reference"] = "hg38"
                context_dict["fasta"] = FASTA_38
                context_dict["fasta_idx"] = FASTA_IDX_38
                context_dict["cytoband"] = CYTOBAND_38
                context_dict["refseq"] = REFSEQ_38

            sample = request.POST['file_name']
            bam_url = request.POST['file_url']
            idx_url = request.POST['idx_url']

            bam_url = str(bam_url).strip()
            idx_url = str(idx_url).strip()

            context_dict["file_name"] = sample.split('.')[0]
            context_dict["file_url"] = bam_url
            context_dict["idx_url"] = idx_url
            context_dict['file_id'] = request.POST['file_id']

            return render(
                request, 'DNAnexus_to_igv/nexus_igv.html', context_dict)

    return render(request, 'DNAnexus_to_igv/nexus_search.html', context_dict)
