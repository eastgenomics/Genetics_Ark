"""
Django app to call primer designer for genetating PDF reports of primer
designs. Primer designer (https://github.com/eastgenomics/primer_designer)
should be set up locally (or the docker image built from its image) and the
path to the dir set in the .env file
"""

import logging
import os
import random
import string
import subprocess

from datetime import datetime
from glob import glob
from zipfile import ZipFile
from pathlib import Path
from django.contrib import messages
# from django.contrib.auth.decorators import login_required
from django.shortcuts import render

import primer_designer.forms as Forms

from ga_core.settings import (
    PRIMER_DESIGNER_REF_PATH, REF_37, DBSNP_37, PRIMER_IMAGE, 
    PRIMER_DESIGNER_OUT_PATH, REF_38, DBSNP_38
    )

error_log = logging.getLogger("ga_error")


# @login_required
def index(request):
    """
    Index Page
    If Form is submitted, return Create page (below)
    Else return Index page
    """
    if request.method == 'POST':
        regions_form = Forms.RegionsForm(request.POST)

        if regions_form.is_valid():
            # One or more valid regions where entered, call function to
            # generate primers
            return create(request, regions_form)
        else:
            messages.add_message(
                request,
                messages.ERROR,
                f"Error in given primer design input {regions_form.data['regions']}"
            )
    else:
        regions_form = Forms.RegionsForm()

    return render(
        request, "primer_designer/index.html", {'regions_form': regions_form})


def random_string():
    """
    Creates a random string

    Returns:
        - random_string (str): str of random characters
    """
    random_string = ''.join(random.choices(
        string.ascii_uppercase + string.ascii_lowercase + string.digits, k=5
    ))

    return random_string.upper()


def time_stamp():
    """
    Return a time stamp to ensure primer designs dont clash

    Returns: (str) time stamp string
    """
    return datetime.now().strftime("%Y%m%d%H%M")


def format_region(region):
    """
    Format region from input form as command (str) for primer designer

    Args: region (str): region passed from Input Form
    Returns: cmd (str): formatted str of cmd for primer designer
    """
    if region.count(':') > 1:
        # format for fusion design, will be in format
        # chr:pos:side:strand chr:pos:side:strand build 'fusion'
        args = region.split()
        cmd = f'--fusion --b1 {args[0]} --b2 {args[1]} --{args[2]}'
    else:
        # either position or range design
        if '-' in region:
            # range design, will be in format chr:pos1-pos2 build
            region, build = region.split()
            chr, pos = region.split(':')
            pos1, pos2 = pos.split('-')

            cmd = f'-c {chr} -r {pos1} {pos2} --{build}'
        else:
            # normal position design, in format chr:pos build
            region, build = region.split()
            chr, pos = region.split(':')

            cmd = f'-c {chr} -p {pos} --{build}'

    return cmd


def call_primer_designer(request, cmd, output_path):
    """
    Calls primer designer with given formatted cmd string

    Args:
        - request: the particular POST request from Input Form
        - cmd (str): region formatted str to pass to primer designer docker cmd
        - output_path: path to output generated PDFs

    Returns: 
        Boolean if Subprocess success or failed
    """
    genome_build = cmd.split(' ')[-1].lstrip('--')

    if genome_build == 'grch37':
        primer_cmd = (
                "docker run "
                f"-v {PRIMER_DESIGNER_REF_PATH}:/reference_files "
                f"-v {output_path}:/home/primer_designer/output "
                f"--env REF_37=/reference_files/{genome_build}/{REF_37} "
                f"--env DBSNP_37=/reference_files/{genome_build}/{DBSNP_37} "
                f"{PRIMER_IMAGE} "
                f"python3 bin/primer_designer_region.py {cmd}"
            )
    else:
        primer_cmd = (
                "docker run "
                f"-v {PRIMER_DESIGNER_REF_PATH}:/reference_files "
                f"-v {output_path}:/home/primer_designer/output "
                f"--env REF_38=/reference_files/{genome_build}/{REF_38} "
                f"--env DBSNP_38=/reference_files/{genome_build}/{DBSNP_38} "
                f"{PRIMER_IMAGE} "
                f"python3 bin/primer_designer_region.py {cmd}"
            )
    
    print(primer_cmd)

    try:
        call = subprocess.run(
            primer_cmd, shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        call.check_returncode()  # raises Error on non-zero exit code
    except subprocess.CalledProcessError as e:
        traceback = e.stderr.decode('utf-8').rstrip('\n')

        if 'Error' in traceback:
            # attempt to not show full ugly traceback, just the error
            # most of the time due to smalt or primer3 error
            err_msg = e.stderr.decode('utf-8').split('Error:')[-1].strip()
        else:
            err_msg = traceback

        error_log.error(f':Primer designer: {traceback}')
        error_log.error(primer_cmd)

        messages.add_message(
            request,
            messages.ERROR,
            f"Error Message: {err_msg}. Error Code: {e.returncode}"
        )
        return False
    return True


# @login_required
def create(request, regions_form):
    """
    Create Page

    Function called when valid form submitted, generates output file 
    then runs primer3 via primer_designer with given regions.
    
    Return:
        link to download PDFs zip
    """
    regions = regions_form.data['regions'].split('\n')
    regions = [x.rstrip('\r').strip() for x in regions if x]

    # unique name of date and random 5 char str
    output_name = f'{time_stamp()}{random_string()}'

    # get parent path in docker container e.g. /home/ga
    parent_path = Path(__file__).parent.parent.absolute()
    print(parent_path)

    # create tmp folder (if not exist) - just in case
    Path(f'{parent_path}/static/tmp').mkdir(parents=True, exist_ok=True)

     # define output dir to host filesystem for primer cmd
    out_dir = f'{PRIMER_DESIGNER_OUT_PATH}/{output_name}/'
    
    # mounted output directory (within docker container)
    mounted_dir = '/home/ga/static/tmp'
    output_zip = f'{mounted_dir}/{output_name}.zip'

    # make directory for all the generated PDF(s) to zip later
    os.mkdir(Path(f'{mounted_dir}/{output_name}')) # empty dir to add reports to

    for region in regions:
        # format each given region as input args for primer designer & call
        cmd = format_region(region)
        output = call_primer_designer(
            request, cmd, out_dir)

        if not output:
            return render(
                request,
                "primer_designer/index.html",
                {'regions_form': regions_form})

    # zip the PDFs in output dir
    with ZipFile(output_zip, 'w') as zfile:
        for pdf in os.listdir(f'{mounted_dir}/{output_name}'):
            zfile.write(f'{mounted_dir}/{output_name}/{pdf}', Path(pdf).name)

    context_dict = {'key': output_name}
    context_dict["outfile_name"] = output_name
    context_dict["url"] = f'/static/tmp/{output_name}.zip'

    return render(request, "primer_designer/create.html", context_dict)
