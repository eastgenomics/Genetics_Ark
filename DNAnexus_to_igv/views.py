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

"""

import itertools
import json
import os
import re
import subprocess

from django.contrib import messages
from django.http import HttpResponse
from django.template import loader
from django.shortcuts import render

import DNAnexus_to_igv.forms as Forms


def get_002_projects():
    """
    Get list of all 002 sequencing projects on DNAnexus to pull bams from

    Args: None

    Returns:
        - project_002_list (list): list of all 002 project names 
    """

    # dx command to find 002 projects
    dx_find_projects = "dx find projects --level VIEW --name 002*"
    
    projects_002 = subprocess.check_output(dx_find_projects, shell=True)

    # get just the project id's from returned string
    projects_002 = projects_002.replace("\n", " ").split(" ")
    project_002_list = [x for x in projects_002 if x.startswith('project-')]

    return project_002_list


def find_dx_bams(project_id, sample_id, dx_data):
    """
    Function to find file and index id for a bam in DNAnexus given a 
    sample id.

    Args:
        - project id (str): DNAnexus project id for 002 project
        - sample_id (str): sample no. from search field
        - dx_data (list): list to append info for each bam to

    Returns:
        - dx_data (list): list containing following for each BAM found:
            - bam_file_id (str): file id of BAM
            - idx_file_id (str): file id of BAM index
            - bam_project_id (str): project id containing BAM
            - idx_project_id (str): project id containing BAM index
            - bam_name (str): human name of BAM file
            - project_name (str): human name of project
            - bam_folder (str): dir path of bam file
            - idx_folder (str): dir path of index file
    """

    # dx commands to retrieve bam and bam.bai for given sample
    dx_find_bam = "dx find data --path {project} --name {sample}*.bam".format(
        project = project_id, sample = sample_id)

    dx_find_idx = "dx find data --path {project} --name {sample}*.bam.bai".format(
        project = project_id, sample = sample_id)

    bam = subprocess.check_output(dx_find_bam, shell=True)
    idx = subprocess.check_output(dx_find_idx, shell=True)

    if bam and idx:
        # if BAM(s) and index found

        # get list from bam and idx with just file ids, needed to handle
        # multiple bams in same project
        bams = bam.replace("\n", " ").split(" ")
        bams_list = [x.strip("()") for x in bams if x.startswith('(file-')]

        idxs = idx.replace("\n", " ").split(" ")
        idx_list = [x.strip("()") for x in idxs if x.startswith('(file-')]

        for bam_id, idx_id in itertools.izip(bams_list, idx_list):
            # for each pair of bam and index, get file attributes

            # dx commands to get readable file and project names
            dx_bam_name = "dx describe --json {}".format(bam_id)
            dx_idx_name = "dx describe --json {}".format(idx_id)
            dx_project_name = "dx describe --json {}".format(project_id)

            # returns a json as a string so convert back to json to select name 
            # and id's out
            bam_json = json.loads(subprocess.check_output(dx_bam_name, shell=True))
            idx_json = json.loads(subprocess.check_output(dx_idx_name, shell=True))

            project_id = bam_json["project"]
            project_json = json.loads(subprocess.check_output(dx_project_name, 
                                                                shell=True))
            
            # get bam and project names to display
            bam_name = bam_json["name"]
            project_name = project_json["name"]

            # get bam and index project ids to check they're from same run
            bam_project_id = bam_json["project"]
            idx_project_id = idx_json["project"]

            # get dir path to display when multiple BAMs found in same project
            bam_folder = bam_json["folder"]
            idx_folder = idx_json["folder"]

            # add required data to list
            dx_data.append({
                            "bam_file_id": bam_id,
                            "idx_file_id": idx_id,
                            "bam_project_id": bam_project_id,
                            "idx_project_id": idx_project_id,
                            "bam_name": bam_name,
                            "project_name": project_name,
                            "bam_folder": bam_folder,
                            "idx_folder": idx_folder
                            })
    return dx_data
  
 
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
            sample_id = sample_id.capitalize() # in case C/G/X is lower case
         
            # get list of 002 projects
            project_002_list = get_002_projects()

            # empty list to add returned data to
            dx_data = []

            for project in project_002_list:
                # find bams in DNAnexus for given sample id, appends to
                # dx_data list
                dx_data = find_dx_bams(project, sample_id, dx_data)

            if len(dx_data) == 0:
                # dx_data empty => bam and index were not found
                messages.add_message(request,
                                messages.ERROR,
                                """Sample {} not found in DNAnexus, either it 
                                is not available or an error has occured. 
                                Please contact the bioinformatics team if you 
                                believe the sample should be available.""".\
                                format(sample_id),
                                extra_tags="alert-danger"
                            )

                return render(request, 'DNAnexus_to_igv/nexus_search.html', 
                                context_dict)

            else:
                # at least 1 BAM was found
                # check each bam and idx pair are from same project,
                # if not exit with error
                for bam in dx_data:
                    if bam["bam_folder"] != bam["idx_folder"]:
                    
                        messages.add_message(request,
                            messages.ERROR,
                            """BAM and index file projects for sample {} do \
                            not match. Please contact the bioinformatics \
                            team.""".format(sample_id),
                            extra_tags="alert-danger"
                            )

                        return render(request, 
                            'DNAnexus_to_igv/nexus_search.html', context_dict)
                    
            if len(dx_data) == 1:
                # one BAM found for sample

                # generate the urls
                bam_url, idx_url = get_dx_urls(
                                                dx_data[0]["bam_file_id"],
                                                dx_data[0]["idx_file_id"]
                                            )
                
                # add variables 
                request.session["bam_url"] = bam_url
                request.session["idx_url"] = idx_url
                request.session["sampleID"] = sample_id
                request.session["bam_name"] = dx_data[0]["bam_name"]
                request.session["project_name"] = dx_data[0]["project_name"]

                context_dict["bam_url"] = bam_url
                context_dict["idx_url"] = idx_url                
                context_dict["sampleID"] = sample_id
                context_dict["bam_name"] = dx_data[0]["bam_name"]
                context_dict["project_name"] = dx_data[0]["project_name"]

                return render(request, 'DNAnexus_to_igv/nexus_search.html',
                                context_dict)
            
            else:
                # multiple BAMs found for sample

                request.session["sampleID"] = sample_id
                context_dict["sampleID"] = sample_id
                
                bam_list = []

                for bam in dx_data:
                    
                    # generate the urls
                    bam_url, idx_url = get_dx_urls(bam["bam_file_id"], 
                                                    bam["idx_file_id"])
                
                    bam_list.append({
                                    "bam_url": bam_url,
                                    "idx_url": idx_url,
                                    "bam_name": bam["bam_name"],
                                    "project_name": bam["project_name"],
                                    "bam_folder": bam["bam_folder"]
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
