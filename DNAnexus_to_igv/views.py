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
import os
import re
import subprocess

from django.contrib import messages
from django.http import HttpResponse
from django.template import loader
from django.utils.safestring import mark_safe
from django.shortcuts import render

import DNAnexus_to_igv.forms as Forms
  
 
def get_dx_urls(bam_file_id, idx_file_id):
    """ 
    Get preauthenticated dx download urls for bam and index
    
    Args:
        - bam_file_id (str): file id of BAM 
        - idx_file_id (str): file if of BAM index
    Returns:
        - bam_url (str): DNAnexus url for downloading BAM file
        - idx_url (str): DNAnexus url for downloading index file
    """

    dx_get_bam_url = "dx make_download_url {}".format(bam_file_id)
    dx_get_idx_url = "dx make_download_url {}".format(idx_file_id)

    # generate the urls
    bam_url = subprocess.check_output(dx_get_bam_url, shell=True).strip()
    idx_url = subprocess.check_output(dx_get_idx_url, shell=True).strip()

    return bam_url, idx_url


def nexus_search(request):
    """
    Main search page function.

    On searching: 
    - a list of 002 project ids is generated from get_002_projects()
    - for each project, dx_find_bams() is used to search for BAMs
    - on finding matching BAM and index, urls are generated with 
      get_dx_urls()
    - renders page with download urls and a button to load igv.js with 
      links
    """

    context_dict = {}
    context_dict["search_form"] = Forms.SearchForm()

    if request.method == 'POST':
        if "search_form" in request.POST:
            # if search button is pressed

            # flush session cache to remove any old search variables
            request.session.flush()

            search_form = Forms.SearchForm(request.POST)

            if search_form.is_valid():
                clean_data = search_form.cleaned_data
            
            sample_id = clean_data["sampleID"]
            sample_id = str(sample_id).strip() # in case spaces
            sample_id = sample_id.upper() # in case C/G/X is lower case

            # load in json with bams
            try:
                json_file = os.path.join(os.path.dirname(__file__),
                                                    "dx_002_bams.json")
                with open(json_file) as json_file:
                    json_bams = json.load(json_file)
            # in case file hasn't been generated
            except IOError:
                messages.add_message(request,
                                messages.ERROR,
                                """An error has occured connecting with
                                DNAnexus to find samples, please contact
                                the bioinformatics team""",\
                                extra_tags="alert-danger"
                            )

                return render(request, 'DNAnexus_to_igv/nexus_search.html', 
                                context_dict)

            try:
                # select bams for sample
                sample_bams = json_bams[sample_id]
            except KeyError:
                # sample_id not in json
                messages.add_message(request,
                                messages.ERROR,
                                mark_safe(
                                """Sample {} not found in DNAnexus, either it\
                                is not available, the full sample name was not\
                                correctly given or another error has occured.\n 
                                Please contact the bioinformatics team if you\
                                believe the sample should be available.""".\
                                format(sample_id)),
                                extra_tags="alert-danger"
                            )

                return render(request, 'DNAnexus_to_igv/nexus_search.html', 
                                context_dict)

                    
            if len(sample_bams) == 1:
                # one BAM found for sample

                # generate the urls
                bam_url, idx_url = get_dx_urls(
                                                sample_bams[0]["bam_file_id"],
                                                sample_bams[0]["idx_file_id"]
                                            )
                
                # add variables 
                request.session["bam_url"] = bam_url
                request.session["idx_url"] = idx_url
                request.session["sampleID"] = sample_id
                request.session["bam_name"] = sample_bams[0]["bam_name"]
                request.session["project_name"] = sample_bams[0]["project_name"]

                context_dict["bam_url"] = bam_url
                context_dict["idx_url"] = idx_url                
                context_dict["sampleID"] = sample_id
                context_dict["bam_name"] = sample_bams[0]["bam_name"]
                context_dict["project_name"] = sample_bams[0]["project_name"]

                return render(request, 'DNAnexus_to_igv/nexus_search.html',
                                context_dict)
            
            else:
                # multiple BAMs found for sample

                request.session["sampleID"] = sample_id
                context_dict["sampleID"] = sample_id
                
                bam_list = []

                for bam in sample_bams:
                    
                    # generate the urls
                    bam_url, idx_url = get_dx_urls(bam["bam_file_id"], 
                                                    bam["idx_file_id"])
                
                    bam_list.append({
                                    "bam_url": bam_url,
                                    "idx_url": idx_url,
                                    "bam_name": bam["bam_name"],
                                    "project_name": bam["project_name"],
                                    "bam_folder": bam["bam_path"]
                                    })

                context_dict["bam_list"] = bam_list
                request.session["bam_list"] = bam_list

                return render(request, 'DNAnexus_to_igv/nexus_search.html',
                                context_dict)

        if "select_bam" in request.POST:
            # BAM has been selected, pass links for it

            # save bam data before flushing session     
            selected_bam = request.POST.get("selected_bam")
            sampleID = request.session["sampleID"]
            session_bams = request.session["bam_list"]

            # flush session cache to remove old search variables
            request.session.flush()

            for bam in session_bams:
                if selected_bam in bam.values():
                    # render page with links to selected bam

                    request.session["sampleID"] = sampleID
                    request.session["bam_name"] = bam["bam_name"]
                    request.session["project_name"] = bam["project_name"]
                    request.session["bam_url"] = bam["bam_url"]
                    request.session["idx_url"] = bam["idx_url"]

                    context_dict["sampleID"] = sampleID
                    context_dict["bam_name"] = bam["bam_name"]
                    context_dict["project_name"] = bam["project_name"]
                    context_dict["bam_url"] = bam["bam_url"]
                    context_dict["idx_url"] = bam["idx_url"]

                    return render(request, 'DNAnexus_to_igv/nexus_search.html', 
                                    context_dict)

        if "igv_ga" in request.POST:
            # view in igv button pressed

            sampleID = request.session["sampleID"]
            bam_url = request.session["bam_url"]
            idx_url = request.session["idx_url"]

            bam_url = str(bam_url).strip
            idx_url = str(idx_url).strip

            context_dict["sampleID"] = sampleID
            context_dict["bam_url"] = bam_url
            context_dict["idx_url"] = idx_url

            return render(
                        request, 'DNAnexus_to_igv/nexus_igv.html', context_dict
                        )

    # just display the form with search box on navigating to page
    return render(request, 'DNAnexus_to_igv/nexus_search.html', context_dict)
