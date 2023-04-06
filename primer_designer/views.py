"""
Django app to call primer designer for genetating PDF reports of primer
designs. Primer designer (https://github.com/eastgenomics/primer_designer)
should be set up locally (or the docker image built from its image) and the
path to the dir set in the .env file
"""

import logging
import json
import random
import string
from datetime import datetime
from pathlib import Path

from django.contrib import messages
from django.shortcuts import render, HttpResponse
from django_q.tasks import async_task, result

import primer_designer.forms as Forms

from ga_core.settings import PRIMER_DOWNLOAD, GRID_SERVICE_DESK

logger = logging.getLogger("general")


def index(request):
    """
    Index Page
    If Form is submitted, return Create page (below)
    Else return Index page
    """

    context_dict = {}
    context_dict['desk'] = GRID_SERVICE_DESK

    if request.method == 'POST':
        regions_form = Forms.RegionsForm(request.POST)

        if regions_form.is_valid():
            # One or more valid regions where entered, call function to
            # generate primers
            return create(request, regions_form)
        else:
            region = regions_form.data['regions']
            messages.add_message(
                request,
                messages.ERROR,
                f"Error in given primer design input {region}"
            )
            context_dict['error'] = True
    else:
        regions_form = Forms.RegionsForm()

    context_dict['regions_form'] = regions_form

    return render(
        request, "primer_designer/index.html", context_dict)


def task(request, task_id: str) -> HttpResponse:
    """
    Function to return task task based on task_id (Django-Q)

    As redis broker does not support task receipt
    Task_status will return task status only when
    task is successfully executed. Timeout or failed
    task will return None

    """
    if result(task_id) is not None:
        task_status, err = result(task_id)
    else:
        task_status = None

    if task_status:
        return HttpResponse(
            json.dumps({'status': 'done'}), content_type='application/json')
    elif task_status is None:
        return HttpResponse(
            json.dumps({'status': 'pending'}), content_type='application/json')
    else:
        return HttpResponse(
            json.dumps(
                {
                    'status': 'failed',
                    'error': err
                    }), content_type='application/json')


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


def create(request, regions_form):
    """
    Create Page

    Function called when valid form submitted, generates output file
    then runs primer3 via primer_designer with given regions.

    Return:
        link to download PDFs zip
    """
    context_dict = {}
    context_dict['desk'] = GRID_SERVICE_DESK
    context_dict['regions_form'] = Forms.RegionsForm()

    regions = regions_form.data['regions'].split('\n')
    regions = [x.rstrip('\r').strip() for x in regions if x]

    # unique name of date and random 5 char str
    output_name = f'{time_stamp()}{random_string()}'

    # define output dir to host filesystem for primer cmd
    PARENT_PATH = '/home/primer_designer/output'

    # make directory for all the generated PDF(s) to zip later
    output_directory = f'{PARENT_PATH}/{output_name}'
    Path(output_directory).mkdir(parents=True, exist_ok=True)

    # put task into Django-q queue
    task_id = async_task(
        'primer_designer.services.call_subprocess',
        output_directory,
        regions,
        output_name)

    context_dict["download_url"] = f'{PRIMER_DOWNLOAD}/tmp/{output_name}.zip'
    context_dict['task_id'] = task_id
    context_dict['output_name'] = output_name

    return render(request, "primer_designer/create.html", context_dict)
