import ast
import datetime
import json
import os
import pprint as pp
import random
import re
import shlex
import shutil
import string
import subprocess
import time

from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

# from ga_core.config import primer_designer_path

import primer_designer.forms as Forms


@login_required
def index(request):
    if request.method == 'POST':
        regions_form = Forms.RegionsForm(request.POST)

        if regions_form.is_valid():
            # One or more valid regions where entered, call function to
            # generate primers
            return create(request, regions_form.data['regions'])

        else:
            error = ast.literal_eval(pp.pformat(regions_form.errors))

            messages.add_message(
                request,
                messages.ERROR,
                """Error in given primer design input: ({})""".format(
                    error["regions"][0]
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
        string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10
    ))

    return random_string


def time_stamp():
    """ Return a time stamp to ensure primer designs dont clash

    Returns:
        - time_string (str): time stamp string
    """
    time_string = time.strftime("%Y%m%d_%H%M%S", time.gmtime())

    return time_string


@login_required
def create(request, regions, infile=None):
    """
    Called when valid form submitted, generates output file then runs
    primer3 via primer_designer with given regions. Subprocess holds the
    page with a loading spinner until completed, then file is written
    and link to download design zip given on returned page.
    """
    tmp_path = "static/tmp/"

    random_tmp = random_string()

    infile = "{}.txt".format(time_stamp())

    if infile is None:
        infile = random_tmp

    outfh = open("{path}{infile}".format(path=tmp_path, infile=infile), "w")
    outfh.write(regions)
    outfh.close()

    # cmd = "/mnt/storage/apps/software/primer_designer/1.1/bulk_design.py\
    #     {infile} {working_dir} ".format(infile=infile, working_dir=path)

    cmd = f"{primer_designer_path} {infile} {tmp_path}"

    context_dict = {'key': random_string}
    context_dict['infile'] = infile

    stderr_file_name = "{}{}.stderr".format(tmp_path, random_tmp)
    stderr_file = open(stderr_file_name, "w+")

    stdout_file_name = "{}{}.stdout".format(tmp_path, random_tmp)
    stdout_file = open(stdout_file_name, "w+")

    context_dict['tmp_key'] = random_tmp

    cmd = shlex.split(cmd)

    p = subprocess.run(
        cmd, shell=False, stderr=stderr_file, stdout=stdout_file)


    outfile_name = infile.replace(".txt", ".zip")
    outfile = os.path.join(tmp_path, outfile_name)

    context_dict["outfile_name"] = outfile_name
    context_dict["url"] = outfile

    return render(request, "primer_designer/create.html", context_dict)
