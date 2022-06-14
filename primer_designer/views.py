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
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.safestring import mark_safe


import primer_designer.forms as Forms
from ga_core.settings import PRIMER_DESIGNER_REF_PATH, REF_37, DBSNP_37, PRIMER_DESIGNER_DIR_PATH

error_log = logging.getLogger("ga_error")


# @login_required
def index(request):
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

            # return render(request, "primer_designer/index.html", {'regions_form': regions_form})
    else:
        regions_form = Forms.RegionsForm()
    
    return render(request, "primer_designer/index.html", {'regions_form': regions_form})


def random_string():
    """
    Creates a random string

    Returns:
        - random_string (str): str of random characters
    """
    random_string = ''.join(random.choices(
        string.ascii_uppercase + string.ascii_lowercase + string.digits, k=5
    ))

    return random_string


def time_stamp():
    """
    Return a time stamp to ensure primer designs dont clash

    Returns: (str) time stamp string
    """
    return datetime.now().strftime("%Y%m%d_%H:%M")


def format_region(region):
    """
    Format region from input form as command str for primer designer

    Args: region (str): region passed from input form
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


def call_primer_designer(request, regions_form, cmd, output_path):
    """
    Calls primer designer with given formatted cmd string

    Args:
        - request: the particular POST request from frontend
        - regions_form (django form): submitted form data
        - cmd (str): region formatted str to pass to primer designer
        - output_path: path to output directory /primer_designer/output
    
    Returns: render HTML for output PDF download link
    """
    primer_cmd = (
            "docker run "
            f"-v {PRIMER_DESIGNER_REF_PATH}:/reference_files "
            f"-v {output_path}:/home/primer_designer/output "
            f"--env REF_37=/reference_files/grch37/{REF_37} "
            f"--env DBSNP_37=/reference_files/grch37/{DBSNP_37} "
            "primer_designer "
            f"python3 bin/primer_designer_region.py {cmd}"
        )

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
    Called when valid form submitted, generates output file then runs
    primer3 via primer_designer with given regions.
    Pageis held with a loading spinner until completed, then file is written
    and link to download design zip given on returned page.
    """
    regions = regions_form.data['regions'].split('\n')
    regions = [x.rstrip('\r').strip() for x in regions if x]

    # unique name of date and random 5 char str
    outname = f'{time_stamp()}-{random_string()}'

    # making an output directory in /primer_designer for output PDF
    Path(f'{Path(__file__).parent.parent.absolute()}/primer_designer/output/').mkdir(parents=True, exist_ok=True)
    primer_output_path = f'{Path(__file__).parent.parent.absolute()}/primer_designer/output/'

    Path(f'{Path(__file__).parent.parent.absolute()}/static/tmp').mkdir(parents=True, exist_ok=True)
    out_dir = f'{Path(__file__).parent.parent.absolute()}/static/tmp/{outname}/'
    out_zip = f'static/tmp/{outname}.zip'
    os.mkdir(Path(out_dir))  # empty dir to add reports to

    primer_path = PRIMER_DESIGNER_DIR_PATH.rstrip('/')

    for region in regions:
        # format each given region as input args for primer designer & call
        cmd = format_region(region)
        output = call_primer_designer(request, regions_form, cmd, primer_output_path)

        if not output:
            return render(request, "primer_designer/index.html", {'regions_form': regions_form})

        # get file just created from primer designer output/ and move to zip
        output_pdf = max(
            glob(f'{primer_path}/output/*pdf'), key=os.path.getctime
        )
        output_pdf = Path(output_pdf).absolute()

        # move from /primer_designer/output to /static/tmp
        subprocess.run(f'mv {output_pdf} {out_dir}', shell=True, check=True)

    # zip the output dir of PDFs
    with ZipFile(out_zip, 'w') as zip_file:
        out_pdfs = glob(f'{out_dir}*.pdf')
        for pdf in out_pdfs:
            zip_file.write(pdf, Path(pdf).name)

    # delete output dir from /static/tmp
    subprocess.run(f'rm -rf {out_dir}', shell=True, check=True)

    context_dict = {'key': outname}
    context_dict["outfile_name"] = outname
    context_dict["url"] = out_zip

    return render(request, "primer_designer/create.html", context_dict)