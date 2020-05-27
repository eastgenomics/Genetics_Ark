# -*- coding: utf-8 -*-
import json
import os
import subprocess

from django.contrib import messages
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render

import DNAnexus_to_igv.forms as Forms

def get_002_projects():
    """
    Get list of all 002 sequencing projects on DNAnexus to pull bams from
    """

    # dx command to find 002 projects
    dx_find_projects = "dx find projects --name 002*"

    projects_002 = subprocess.check_output(dx_find_projects, shell=True)
    
    # get just the project id's from returned string
    projects_002 = projects_002.replace("\n", " ").split(" ")
    project_002_list = filter(lambda x: x.startswith('project-'), projects_002)

    return project_002_list

def find_dx_bams(project_id, sample_id):
    """
    Function to find file and index id for a bam in DNAnexus given a 
    sample id.

    Args:
        - project id (str): DNAnexus project id for 002 project
        - sample_id (str): sample no. from search field

    Returns:
        - bam_file_id (str): file id of BAM
        - idx_file_id (str): file id of BAM index
        - bam_project_id (str): project id containing BAM
        - idx_project_id (str): project id containing BAM index
        - bam_name (str): human name of BAM file
        - project_name (str): human name of project
    """
    # dx commands to retrieve bam and bam.bai for given sample
    dx_find_bam = "dx find data --path {} --name *{}*_markdup.bam".format(
        project_id, sample_id)

    dx_find_idx = "dx find data --path {} --name *{}*_markdup.bam.bai".format(
        project_id, sample_id)

    bam = subprocess.check_output(dx_find_bam, shell=True)
    idx = subprocess.check_output(dx_find_idx, shell=True)

    if bam and idx:
        # if bam found

        # get just the bam and index id
        bam_file_id = bam.split( )[-1].strip("()")
        idx_file_id = idx.split( )[-1].strip("()")

        # dx commands to get readable file and project names
        dx_bam_name = "dx describe --json {}".format(bam_file_id)
        dx_id_name = "dx describe --json {}".format(idx_file_id)
        dx_project_name = "dx describe --json {}".format(project_id)

        # returns a json as a string so convert back to json to select name 
        # and id's out
        bam_json = json.loads(subprocess.check_output(dx_bam_name, shell=True))
        idx_json = json.loads(subprocess.check_output(dx_id_name, shell=True))
        project_json = json.loads(subprocess.check_output(dx_project_name, 
                                                            shell=True))

        # get bam and project names to display
        bam_name = bam_json["name"]
        project_name = project_json["name"]

        # get bam and index project ids to check they're from same run
        bam_project_id = bam_json["project"]
        idx_project_id = idx_json["project"]
        
    else:
        # bam not found
        bam_file_id, idx_file_id, bam_name, bam_project_id,\
        idx_project_id, project_name = None, None, None, None, None, None

    return bam_file_id, idx_file_id, bam_project_id,\
            idx_project_id, bam_name, project_name
  
 
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
    bam_url = subprocess.check_output(dx_get_bam_url, shell=True)
    idx_url = subprocess.check_output(dx_get_idx_url, shell=True)

    return bam_url, idx_url


def nexus_search(request):
    """

    Main search page function.

    On searching: 
    - a list of 002 project ids is generated from get_002_projects()
    - for each project, dx_find_bams() is used to search for BAMs
    - on finding matching BAM and index, urls are generated with get_dx_urls()
    - renders page with download urls and a button to load igv.js with links

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
            sample_id = sample_id.upper() # in case X no. is lower case
         
            # get list of 002 projects
            project_002_list = get_002_projects()

            for project in project_002_list:
                # find bams in DNAnexus for given sample id
                
                # kinda clunky but works, currently no option in dx find 
                # data to pass array of projects and apparently this is 
                # best practice
                bam_file_id, idx_file_id, bam_project_id, idx_project_id,\
                bam_name, project_name = find_dx_bams(project, sample_id)

                if bam_file_id is not None and idx_file_id is not None:
                    # bam and index found, no need to search rest of projects
                    break

            if bam_file_id is not None and idx_file_id is not None:
                # if bam and index were found

                if bam_project_id != idx_project_id:
                    # bam and index not from same run

                    messages.add_message(request,
                                messages.ERROR,
                                """BAM and index file projects do not match. 
                                Please contact the bioinformatics team.""".\
                                format(sample_id),
                                extra_tags="alert-danger"
                            )

                    return render(request, 'DNAnexus_to_igv/nexus_search.html', 
                                    context_dict)
                
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
                # if bam and index were not found
                messages.add_message(request,
                                messages.ERROR,
                                """Sample {} not found in DNAnexus, either it 
                                is not available or an error has occured. 
                                Please contact the bioinformatics team if you 
                                believe the sample should be available.""".\
                                format(sample_id),
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

            return render(
                        request, 'DNAnexus_to_igv/nexus_igv.html', context_dict
                        )

    # just display the form with search box on navigating to page
    return render(request, 'DNAnexus_to_igv/nexus_search.html', context_dict)