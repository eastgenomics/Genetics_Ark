# -*- coding: utf-8 -*-
import json
import os
import subprocess

from django.contrib import messages
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render

import DNAnexus_to_igv.forms as Forms

def find_dx_bams(sample_id):
    """
    Function to find file and index id for a bam in DNAnexus given a sample id
    Args:
        - sample_id
    Returns:
        - bam_file_id, idx_file_id, bam_project_id, idx_project_id, bam_name, project_name
    """
    # dx commands to retrieve bam and bam.bai for given sample
    dx_find_bam = "dx find data --all-projects --name *{}*_markdup.bam".format(sample_id)
    dx_find_idx = "dx find data --all-projects --name *{}*_markdup.bam.bai".format(sample_id)

    bam = subprocess.check_output(dx_find_bam, shell=True)
    idx = subprocess.check_output(dx_find_idx, shell=True)

    if bam and idx:
        # if bam found

        # get just the file and index id
        split_bam = bam.split( )[-1].strip("()").split(":")
        split_idx = idx.split( )[-1].strip("()").split(":")

        bam_project_id = split_bam[0]
        idx_project_id = split_idx[0]

        bam_file_id = split_bam[1]
        idx_file_id = split_idx[1]            

        # dx commands to get readable file and project names
        dx_bam_name = "dx describe --json {}".format(bam_file_id)
        dx_project_name = "dx describe --json {}".format(bam_project_id)

        # returns a json as a string so convert back to json to select name out
        bam_name = json.loads(subprocess.check_output(dx_bam_name, shell=True))
        project_name = json.loads(subprocess.check_output(dx_project_name, shell=True))
        
        # get bam and project names to display
        bam_name = bam_name["name"]
        project_name = project_name["name"]

    else:
        # bam not found
        bam_file_id, idx_file_id, bam_name, bam_project_id, idx_project_id, project_name = None, None, None, None, None, None

    return bam_file_id, idx_file_id, bam_project_id, idx_project_id, bam_name, project_name
  
 
def get_dx_urls(bam_file_id, idx_file_id):
    """ 
    Get preauthenticated dx download urls for bam and index from given id's
    Args:
        - bam_file_id, idx_file_id
    Returns:
        - bam_url, idx_url
    """

    dx_get_bam_url = "dx make_download_url {}".format(bam_file_id)
    dx_get_idx_url = "dx make_download_url {}".format(idx_file_id)

    # generate the urls
    bam_url = subprocess.check_output(dx_get_bam_url, shell=True)
    idx_url = subprocess.check_output(dx_get_idx_url, shell=True)

    return bam_url, idx_url


def nexus_search(request):
    """
    Main search page function
    """

    context_dict = {}
    context_dict["search_form"] = Forms.SearchForm()

    if request.method == 'POST':
        if "search_form" in request.POST:
            # if search button is pressed
            search_form = Forms.SearchForm(request.POST)

            if search_form.is_valid():
                clean_data = search_form.cleaned_data
            
            sample_id = clean_data["sampleID"]
            sample_id = str(sample_id).strip() # in case they put spaces
            sample_id = sample_id.upper() # in case X is given lower case
         
            # find bams in DNAnexus with given sample id
            bam_file_id, idx_file_id, bam_project_id, idx_project_id, bam_name, project_name = find_dx_bams(sample_id)

            if bam_file_id and idx_file_id:

                if bam_project_id != idx_project_id:
                    # bam and index not from same run

                    messages.add_message(request,
                                messages.ERROR,
                                "BAM and index file projects do not match. Please contact the bioinformatics team.".format(sample_id),
                                extra_tags="alert-danger"
                            )

                    return render(request, 'DNAnexus_to_igv/nexus_search.html', context_dict)
                
                else:
                    # bam and index match, generate the urls
                    bam_url, idx_url = get_dx_urls(bam_file_id, idx_file_id)

                    # add variables 
                    request.session["sampleID"] = sample_id
                    request.session["bam_url"] = bam_url
                    request.session["idx_url"] = idx_url
                    request.session["bam_name"] = bam_name
                    request.session["project_name"] = project_name

                    context_dict["sampleID"] = sample_id
                    context_dict["bam_url"] = bam_url
                    context_dict["idx_url"] = idx_url
                    context_dict["bam_name"] = bam_name
                    context_dict["project_name"] = project_name

            else:
                # if bam and index not found
                messages.add_message(request,
                                messages.ERROR,
                                "Sample {} not found in DNAnexus, either it is not available or an error has occured. Please contact the bioinformatics team.".format(sample_id),
                                extra_tags="alert-danger"
                            )
            
        if "igv_ga" in request.POST:
            # view in igv button pressed

            sampleID = request.session["sampleID"]
            bam_url = request.session["bam_url"]
            idx_url = request.session["idx_url"]

            bam_url = str(bam_url).strip
            idx_url =str(idx_url).strip

            context_dict["sampleID"] = sampleID
            context_dict["bam_url"] = bam_url
            context_dict["idx_url"] = idx_url

            return render(request, 'DNAnexus_to_igv/nexus_igv.html', context_dict)

    # just display the form with search box on navigating to page
    return render(request, 'DNAnexus_to_igv/nexus_search.html', context_dict)