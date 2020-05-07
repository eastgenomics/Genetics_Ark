# -*- coding: utf-8 -*-
import os
import subprocess

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
        - bam_file_id, idx_file_id
    """
    # dx commands to retrieve bam and bam.bai for given sample
    dx_find_bam = "dx find data --all-projects --name *{}*_markdup.bam".format(sample_id)
    dx_find_idx = "dx find data --all-projects --name *{}*_markdup.bam.bai".format(sample_id)

    bam = subprocess.check_output(dx_find_bam, shell=True)
    idx = subprocess.check_output(dx_find_idx, shell=True)

    # get just the file id and index id
    split_bam = bam.split( )[-1].strip("()").split(":")
    split_idx = idx.split( )[-1].strip("()").split(":")

    bam_file_id = split_bam[1]
    idx_file_id = split_idx[1]
    
    return bam_file_id, idx_file_id


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

    # call dx api to generate the urls
    bam_url = subprocess.check_output(dx_get_bam_url, shell=True)
    idx_url = subprocess.check_output(dx_get_idx_url, shell=True)

    return bam_url, idx_url


def nexus_search(request):
    context_dict = {}
    context_dict["search_form"] = Forms.SearchForm()

    if request.method == 'POST':
        if "search_form" in request.POST:
            # if search button is pressed
            search_form = Forms.SearchForm(request.POST)

            if search_form.is_valid():
                # check what is input is valid
                clean_data = search_form.cleaned_data
            
            sample_id = clean_data["sampleID"]

            # find bams in DNAnexus with given sample id
            bam_file_id, idx_file_id = find_dx_bams(sample_id)

            # get the urls for bam and index
            bam_url, idx_url = get_dx_urls(bam_file_id, idx_file_id)

            request.session["sampleID"] = clean_data["sampleID"]
            request.session["bam_url"] = bam_url
            request.session["idx_url"] = idx_url

            context_dict["sampleID"] = clean_data["sampleID"]
            context_dict["bam_url"] = bam_url
            context_dict["idx_url"] = idx_url

            
        if "igv_ga" in request.POST:
            print "getting"

            sampleID = request.session["sampleID"]
            bam_url = request.session["bam_url"]
            idx_url = request.session["idx_url"]

            bam_url = str(bam_url).strip
            idx_url =str(idx_url).strip

            context_dict["sampleID"] = sampleID
            context_dict["bam_url"] = bam_url
            context_dict["idx_url"] = idx_url

            print type(bam_url)
            print type(idx_url)
            print bam_url
            print idx_url

            return render(request, 'DNAnexus_to_igv/nexus_igv.html', context_dict)

    # just display the form with search box on navigating to page
    return render(request, 'DNAnexus_to_igv/nexus_search.html', context_dict)