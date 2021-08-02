import ast
from datetime import datetime
from glob import glob
import os
from pathlib import Path
import pprint as pp
import random
import string
import subprocess

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.safestring import mark_safe


import primer_designer.forms as Forms

from ga_core.settings import PRIMER_DESIGNER_DIR_PATH


@login_required
def index(request):
    if request.method == 'POST':
        regions_form = Forms.RegionsForm(request.POST)

        if regions_form.is_valid():
            # One or more valid regions where entered, call function to
            # generate primers
            return create(request, regions_form)
        else:
            error = ast.literal_eval(pp.pformat(regions_form.errors))

            messages.add_message(
                request,
                messages.ERROR,
                mark_safe(
                    f"Error in given primer design input: {error['regions'][0]}"
                ),
                extra_tags="alert-danger"
            )

            return render(request, "primer_designer/index.html", {
                'regions_form': regions_form
            })
    else:
        return render(request, "primer_designer/index.html", {
            'regions_form': Forms.RegionsForm()
        })


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


@login_required
def create(request, regions_form):
    """
    Called when valid form submitted, generates output file then runs
    primer3 via primer_designer with given regions. Subprocess holds the
    page with a loading spinner until completed, then file is written
    and link to download design zip given on returned page.
    """
    regions = regions_form.data['regions'].split('\n')
    regions = [x.rstrip('\r').strip() for x in regions]
    region_cmds = []

    for region in regions:
        # format each given region as input args for primer designer
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
                # normal position design
                region, build = region.split()
                chr, pos = region.split(':')

                cmd = f'-c {chr} -p {pos} --{build}'

        region_cmds.append(cmd)

    # unique name of date and random 5 char str
    outname = f'{time_stamp()}-{random_string()}'
    out_dir = f'{Path(__file__).parent.parent.absolute()}/static/tmp/{outname}/'
    out_zip = f'static/tmp/{outname}.zip'

    os.mkdir(Path(out_dir))  # empty dir to add reports to

    for cmd in region_cmds:
        # run primer designer for each given region
        primer_path = PRIMER_DESIGNER_DIR_PATH.rstrip('/')
        primer_cmd = f'python3 {primer_path}/bin/primer_designer_region.py {cmd}'

        try:
            # calling primer designer script, probably should import and run
            # but its messy ¯\_(ツ)_/¯
            call = subprocess.run(
                primer_cmd, shell=True, check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            call.check_returncode()  # raises Error on non-zero exit code
        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode('utf-8').rstrip('\n')
            if 'Error' in err_msg:
                # attempt to not show full ugly traceback, just the error
                err_msg = e.stderr.decode('utf-8').split('Error')[-1]

            messages.add_message(
                request,
                messages.ERROR,
                mark_safe((
                   f"Error in designing primers. Error code: {e.returncode}</br>"
                   f"Error message: {err_msg}</br>{cmd}"
                )),
                extra_tags="alert-danger"
            )

            return render(request, "primer_designer/index.html", {
                'regions_form': regions_form
            })

        # get file just created from primer designer output/ and move to zip
        output_pdf = max(
            glob(f'{primer_path}/output/*pdf'), key=os.path.getctime
        )
        output_pdf = Path(output_pdf).absolute()

        subprocess.run(f'mv {output_pdf} {out_dir}', shell=True, check=True)

    # zip the output dir of PDFs
    subprocess.run(f'zip -j {out_zip} {out_dir}*.pdf', shell=True, check=True)

    # delete output dir from tmp/
    subprocess.run(f'rm -r {out_dir}', shell=True, check=True)

    context_dict = {'key': outname}
    context_dict["outfile_name"] = outname
    context_dict["url"] = out_zip

    return render(request, "primer_designer/create.html", context_dict)
