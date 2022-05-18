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
import itertools
import json
import logging
import os
from pathlib import Path
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.conf import settings
import dxpy as dx

import DNAnexus_to_igv.forms as Forms

from ga_core.settings import (
    AUTH_TOKEN, FASTA_37, FASTA_IDX_37, CYTOBAND_37, REFSEQ_37,
    FASTA_38, FASTA_IDX_38, CYTOBAND_38, REFSEQ_38
)

error_log = logging.getLogger("ga_error")

# set env variable for dxpy authentication
DX_SECURITY_CONTEXT = {
    "auth_token_type": "Bearer",
    "auth_token": AUTH_TOKEN
}

# set token to env
dx.set_security_context(DX_SECURITY_CONTEXT)


def get_dx_urls(request, sample_id, bam_file_id, bam_file_name, idx_file_id,
                idx_file_name, project_id):
    """
    Get preauthenticated dx download urls for bam and index

    Args:
        - bam_file_id (str): file id of BAM
        - idx_file_id (str): file id of BAM index
    Returns:
        - bam_url (str): DNAnexus url for downloading BAM file
        - idx_url (str): DNAnexus url for downloading index file
    """
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
        # error connecting to DNAnexus or in generating url
        messages.add_message(
            request,
            messages.ERROR,
            """Error in generating DNAnexus URLs for sample {} in project {}.
            Please contact the bioinformatics team""".format(
                sample_id, project_id
            )
        )
        error_log.error(re.sub(
            r'\s+', ' ', """Error generating dx download URLS for sample
            {} in project {}""".format(sample_id, project_id)
        ))
        logging.error(e)

        bam_url = None
        idx_url = None

    return bam_url, idx_url


@login_required
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
    context_dict["search_form"] = Forms.SearchForm()
    context_dict["url_form"] = Forms.urlForm()

    if request.method == 'POST':
        if "search_form" in request.POST:
            # if search button is pressed

            # flush session cache to remove any old search variables
            for key in list(request.session.keys()):
                if "auth" not in key:
                    del request.session[key]

            search_form = Forms.SearchForm(request.POST)

            if search_form.is_valid():
                clean_data = search_form.cleaned_data

            sample_id = clean_data["sampleID"]
            sample_id = str(sample_id).strip()  # in case spaces

            try:
                # load in json with all bams and dx attributes needed to
                # search and generate dx download links
                # if json is not present it will raise IOError
                json_file = f'{Path(__file__).parent.absolute()}/jsons/dx_002_bams.json'

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
                error_log.error(re.sub(
                    r'\s+', ' ', """Failed to load sample list from JSON, most
                    likely the JSON has not been generated with
                    find_dx_002_bams.py"""
                ))
                logging.error(IOe)

                return render(
                    request, 'DNAnexus_to_igv/nexus_search.html', context_dict
                )

            # select bams matching sample id, return original entry from
            # JSON by matching against upper name and search term
            # (structure of json may be found in find_dx_bams.py)
            sample_bams = [
                bam for _, bam in json_bams.items()
                if sample_id.upper() in bam[0]['bam_name'].upper()
            ]

            # no bams found
            if len(sample_bams) == 0:
                messages.add_message(
                    request,
                    messages.ERROR,
                    mark_safe(
                        """Sample {} not found in DNAnexus, either it is not\
                        available, the sample name was not correctly\
                        given or another error has occured. Please contact\
                        the bioinformatics team if you believe the sample\
                        should be available.""".format(sample_id)),
                    extra_tags="alert-danger"
                )
                error_log.error((re.sub(
                    r'\s+', ' ', """Sample {} not found in JSON. Either sample
                    name mistyped or an error in finding the BAMs for the
                    sample, possibly missing index.""".format(sample_id)
                )))

                return render(request, 'DNAnexus_to_igv/nexus_search.html',
                              context_dict)

            # one sample found with one bam, generate the urls
            if len(sample_bams[0]) == 1 and len(sample_bams) == 1:
                sample_dict = sample_bams[0][0]

                bam_url, idx_url = get_dx_urls(
                    request,
                    sample_id,
                    sample_dict["bam_file_id"],
                    sample_dict["bam_name"],
                    sample_dict["idx_file_id"],
                    sample_dict["idx_name"],
                    sample_dict["project_id"]
                )

                if bam_url is None or idx_url is None:
                    # error generating urls, display message
                    messages.add_message(
                        request,
                        messages.ERROR,
                        mark_safe(
                            "Error generating download URLs for sample "
                            f"{sample_id}, please contact the bioinformatics "
                            "team for help."), extra_tags="alert-danger"
                    )

                    error_log.error(
                        f"Error generating download urls for {sample_id}, "
                        "most likely issue is dx token has expired or issue "
                        "connecting to DNAnexus."
                    )

                    return render(
                        request, 'DNAnexus_to_igv/nexus_search.html',
                        context_dict
                    )

                # add variables
                request.session["bam_url"] = bam_url
                request.session["idx_url"] = idx_url
                request.session["sampleID"] = sample_id
                request.session["bam_name"] = sample_dict["bam_name"]
                request.session["project_name"] = sample_dict["project_name"]

                context_dict["bam_url"] = bam_url
                context_dict["idx_url"] = idx_url
                context_dict["sampleID"] = sample_id
                context_dict["bam_name"] = sample_dict["bam_name"]
                context_dict["project_name"] = sample_dict["project_name"]
                context_dict['bam_folder'] = sample_dict['bam_folder']
                context_dict['bam_archival_state'] = sample_dict['bam_archival_state']
                context_dict['idx_archival_state'] = sample_dict['idx_archival_state']

                return render(request, 'DNAnexus_to_igv/nexus_search.html',
                              context_dict)

            else:
                # multiple BAMs and / or samples found

                request.session["sampleID"] = sample_id
                context_dict["sampleID"] = sample_id

                bam_list = []

                for bam in itertools.chain.from_iterable(sample_bams):
                    # can be mix of lists and nested lists

                    if "dev" in bam["project_name"]:
                        # if dev data project add development after path
                        path = "({}) - DEVELOPMENT".format(
                            bam["bam_path"]
                        )
                    else:
                        path = "({})".format(bam["bam_path"])

                    bam_list.append({
                        "bam_name": bam["bam_name"],
                        "idx_name": bam["idx_name"],
                        "project_name": bam["project_name"],
                        "project_id": bam["project_id"],
                        "bam_folder": path.lstrip('(').rstrip(')'),
                        "idx_id": bam["idx_file_id"],
                        "bam_id": bam["bam_file_id"],
                        "bam_archival_state": bam["bam_file_archival_status"],
                        "idx_archival_state": bam["idx_file_archival_status"]
                    })

                context_dict["bam_list"] = bam_list
                context_dict["bam_no"] = len(bam_list)
                request.session["bam_list"] = bam_list

                return render(request, 'DNAnexus_to_igv/nexus_search.html',
                              context_dict)

        if "select_bam" in request.POST:
            # BAM has been selected, save bam data before flushing
            # session
            selected_bam = request.POST.get("selected_bam_input")
            session_bams = request.session["bam_list"]

            for bam in session_bams:
                if selected_bam in bam.values():
                    sampleID = bam["bam_name"].split('.')[0]
                    print(sampleID)
                    # generate urls for selected sample
                    bam_url, idx_url = get_dx_urls(
                        request,
                        sampleID,
                        bam["bam_id"],
                        bam["bam_name"],
                        bam["idx_id"],
                        bam["idx_name"],
                        bam["project_id"]
                    )

                    # render page with links to selected bam
                    request.session["sampleID"] = sampleID
                    request.session["bam_name"] = bam["bam_name"]
                    request.session["project_name"] = bam["project_name"]
                    request.session["bam_url"] = bam_url
                    request.session["idx_url"] = idx_url

                    context_dict["sampleID"] = sampleID
                    context_dict["bam_name"] = bam["bam_name"]
                    context_dict["project_name"] = bam["project_name"]
                    context_dict["bam_url"] = bam_url
                    context_dict["idx_url"] = idx_url
                    context_dict['bam_folder'] = bam['bam_folder']
                    context_dict['bam_id'] = bam['bam_id']
                    context_dict['idx_id'] = bam['idx_id']
                    context_dict['bam_archival_state'] = bam['bam_archival_state']
                    context_dict['idx_archival_state'] = bam['idx_archival_state']

                    return render(request, 'DNAnexus_to_igv/nexus_search.html', context_dict)

        if "url_form_37" in request.POST or "url_form_38" in request.POST:
            # if direct url button is pressed
            url_form = Forms.urlForm(request.POST)

            if url_form.is_valid():
                clean_data = url_form.cleaned_data

            bam_url = str(clean_data["bam_url_form"]).strip()
            idx_url = str(clean_data["idx_url_form"]).strip()

            if "bai" not in bam_url and "bai" in idx_url:
                # check urls in correct fields
                context_dict["sampleID"] = "direct urls"
                context_dict["bam_url"] = bam_url
                context_dict["idx_url"] = idx_url

                # check for reference by button name pressed
                if "url_form_37" in request.POST:
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

                return render(request, 'DNAnexus_to_igv/nexus_igv.html',
                              context_dict)
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    """An error has occured loading IGV from the\
                        provided URLs. Please check URLs are correct\
                        and have been pasted in the correct fields.
                        URLs used:
                        BAM: {bam_url}
                        Index: {idx_url}""".format(
                        bam_url=bam_url, idx_url=idx_url
                    ), extra_tags="alert-danger"
                )

                error_log.error(
                    "Error loading IGV from pasted urls, most likely pasted "
                    f"in wrong fields. BAM URL: {bam_url}. Index URL: "
                    f"{idx_url}"
                )

                return render(request, 'DNAnexus_to_igv/nexus_search.html',
                              context_dict)


        if "igv_ga_37" in request.POST or "igv_ga_38" in request.POST:
            # view in igv button pressed

            # check for reference by button name pressed
            if "igv_ga_37" in request.POST:
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

            sample = request.session["bam_name"]
            bam_url = request.session["bam_url"]
            idx_url = request.session["idx_url"]

            bam_url = str(bam_url).strip()
            idx_url = str(idx_url).strip()

            context_dict["sampleID"] = sample.split('.')[0]
            context_dict["bam_url"] = bam_url
            context_dict["idx_url"] = idx_url

            return render(request, 'DNAnexus_to_igv/nexus_igv.html',
                          context_dict)

    # just display the form with search box on navigating to page
    return render(request, 'DNAnexus_to_igv/nexus_search.html', context_dict)
