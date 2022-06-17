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
    PRIMER_DESIGNER_REF_PATH, REF_37, DBSNP_37, PRIMER_IMAGE
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
                "Error in given primer design input"
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
    primer_cmd = (
            "docker run "
            f"-v {PRIMER_DESIGNER_REF_PATH}:/reference_files "
            f"-v {output_path}:/home/primer_designer/output "
            f"--env REF_37=/reference_files/grch37/{REF_37} "
            f"--env DBSNP_37=/reference_files/grch37/{DBSNP_37} "
            f"{PRIMER_IMAGE} "
            f"python3 bin/primer_designer_region.py {cmd}"
        )

    try:
        call = subprocess.run(
            primer_cmd, shell=True, check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        call.check_returncode()  # raises Error on non-zero exit code
    except subprocess.CalledProcessError as e:
        # example traceback from primer after cleaning
        # RuntimeError: Error in generating primers - 
        # no primers generated by primer3 OR no mappings output from smalt. Exiting now.
        traceback = e.stderr.decode('utf-8').rstrip('\n')

        if 'Error' in traceback:
            # attempt to not show full ugly traceback, just the error
            err_msg = e.stderr.decode('utf-8').split('Error:')[-1].strip()

        error_log.error(f':Primer designer: {traceback}')
        error_log.error(primer_cmd)

        messages.add_message(
            request,
            messages.ERROR,
            f"ERROR MSG: {err_msg}. ERROR CODE: {e.returncode}"
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
    outname = f'{time_stamp()}{random_string()}'

    parent_path = Path(__file__).parent.parent.absolute()

    # make tmp folder (if not exist) to put generated PDF
    Path(f'{parent_path}/static/tmp').mkdir(parents=True, exist_ok=True)
    out_dir = f'{parent_path}/static/tmp/{outname}/'
    out_zip = f'static/tmp/{outname}.zip'

    # make directory for all the generated PDF(s) to zip later
    os.mkdir(Path(out_dir))  # empty dir to add reports to

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
    with ZipFile(out_zip, 'w') as zip_file:
        out_pdfs = glob(f'{out_dir}*.pdf')
        for pdf in out_pdfs:
            zip_file.write(pdf, Path(pdf).name)

    # the above will generate a zip file containing
    # all generated PDFs in /static/tmp

    # since we already got a zip file, we don't need
    # those generated PDFs in /static/tmp/{out_dir} anymore
    # below function delete this directory which contain
    # all the generated PDFs in it
    subprocess.run(f'rm -rf {out_dir}', shell=True, check=True)

    context_dict = {'key': outname}
    context_dict["outfile_name"] = outname
    context_dict["url"] = out_zip

    return render(request, "primer_designer/create.html", context_dict)
