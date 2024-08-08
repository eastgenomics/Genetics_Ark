import json
import logging
import re
import requests
from pathlib import Path
import dxpy as dx

from django.contrib import messages
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

# forms import
from DNAnexus_to_igv.forms import UrlForm, SearchForm

from ga_core.settings import (
    FASTA_37,
    FASTA_IDX_37,
    CYTOBAND_37,
    REFSEQ_37,
    FASTA_38,
    FASTA_IDX_38,
    CYTOBAND_38,
    REFSEQ_38,
    DNANEXUS_TOKEN,
    SLACK_TOKEN,
    DEBUG,
    GENOMES,
    REFSEQ_INDEX_37,
    REFSEQ_INDEX_38,
    GRID_SERVICE_DESK,
)

logger = logging.getLogger("general")

PAGINATION = 20


def dx_login(
    dnanexus_token: str, slack_token: str, debug: bool, cron: bool = False
) -> None:
    """
    Function to check DNANexus auth token. Send Slack notification
    if auth failed.

    dnanexus_token: dnanexus api token
    slack_token: slack api token
    debug: if run in debug, send to #egg-test
    cron: if the function is ran from cron container

    """
    DX_SECURITY_CONTEXT = {
        "auth_token_type": "Bearer",
        "auth_token": dnanexus_token,
    }

    # set token to env
    dx.set_security_context(DX_SECURITY_CONTEXT)

    try:
        dx.api.system_whoami()
    except Exception as err:
        message = (
            "Genetics Ark: Failed connecting to DNAnexus\n"
            f"Error Message: `{err}`"
        )
        logger.error(err)

        if cron:
            if not debug:
                post_message_to_slack("egg-alerts", message, slack_token)
            else:
                post_message_to_slack("egg-test", message, slack_token)
        return False

    return True


def post_message_to_slack(
    channel: str, message: str, slack_token: str
) -> None:
    """
    Function to send Slack notification
    Taken from:
    https://github.com/eastgenomics/ansible-run-monitoring/blob/main/util.py
    Inputs:
        channel: egg-alerts
        message: text
        slack_token: slack api token
    Returns:
        dict: slack api response
    """

    try:
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            {"token": slack_token, "channel": f"#{channel}", "text": message},
        ).json()

        if response["ok"]:
            logger.info(f"POST request to channel #{channel} successful")
            return
        else:
            # slack api request failed
            error_code = response["error"]
            logger.error(f"Error Code From Slack: {error_code}")

    except Exception as e:
        # endpoint request fail from server
        logger.error(f"Error sending POST request to channel #{channel}")
        logger.error(e)


def get_dx_urls(
    project_id: str,
    file_id: str,
    filename: str,
) -> dict:
    """
    Get preauthenticated dx download urls for file and its index

    Args:
        - sample-id (str): for error reporting purpose
        - bam_file_id (str): BAM/CNV file-id
        - idx_file_id (str): BAM/CNV index file-id
        - bam_file_name (str): BAM/CNV filename
        - idx_file_name (str): BAM/CNV index filename
        - project_id (str): project-id
    Returns:
        - bam_url (str): DNAnexus url for downloading BAM/CNV file
        - idx_url (str): DNAnexus url for downloading its index file
    """

    if dx_login(DNANEXUS_TOKEN, SLACK_TOKEN, DEBUG):
        file_object = dx.bindings.dxfile.DXFile(
            dxid=file_id, project=project_id
        )

        try:
            file_info = file_object.get_download_url(
                duration=3600,
                preauthenticated=True,
                project=project_id,
                filename=filename,
            )
        except Exception as err:
            logger.error(
                f"The input-sample-name {filename} with file-id {file_id}"
                f"& project-id {project_id} produced"
                " an error when generating a DNANexus"
                f" download link. Error Message returned {err}"
            )

            return {"error": err}
        else:
            download_url = file_info[0]
            return {"url": download_url}

    else:
        msg = "Failed to login with DNAnexus API token. Please check token."
        logger.error(msg)
        return {
            "error": msg
        }

def sanitize_sample_id(original):
    """
    Strip out spaces from the sample ID entered by the user, and if the sample
    begins with 'SP-', remove this.

    Args:
        - original (str): sample ID as retrieved from the search form
    Returns:
        - sample_id (str): sample ID after sanitizing
    """
    sample_id = str(original).strip()
    if sample_id.startswith("SP_"):
        sample_id = sample_id.replace("SP_", "")
    return sample_id

@login_required()
def index(request):
    """
    Main index page for igv view
    """
    context_dict = {}
    context_dict["search_form"] = SearchForm()
    context_dict["url_form"] = UrlForm()
    context_dict["desk"] = GRID_SERVICE_DESK

    return render(request, "DNAnexus_to_igv/nexus_search.html", context_dict)


@login_required()
def search(request):
    """
    Search function when sample id entered
    """

    if request.method == "POST":
        context_dict = {}
        context_dict["search_form"] = SearchForm()
        context_dict["url_form"] = UrlForm()
        context_dict["desk"] = GRID_SERVICE_DESK

        entered_sample_id = request.POST["sample_id"]
        sample_id = sanitize_sample_id(entered_sample_id)

        try:
            # load in json with all bams and dx attributes needed to
            # search and generate dx download links
            # if json is not present it will raise IOError
            json_path = Path(__file__).parent.absolute()
            json_file = f"{json_path}/jsons/dx_002_bams.json"
            logger.info(f"JSON FILE PATH: {json_file}")

            with open(json_file) as json_file:
                json_bams = json.load(json_file)

        except IOError as IOe:
            messages.add_message(
                request,
                messages.ERROR,
                "JSON file containing samples not found.",
            )
            context_dict["error"] = True
            logger.error(IOe)

            return render(
                request, "DNAnexus_to_igv/nexus_search.html", context_dict
            )

        if request.POST["sample_type"] == "BAM":
            # select bams matching sample id, return original entry from
            # JSON by matching against upper name and search term
            # (structure of json may be found in find_dx_bams.py)
            # change to search partial
            sample_data = [
                value
                for key, value in json_bams["BAM"].items()
                if sample_id.upper() in key.upper()
            ]
        else:
            # CNV handling
            sample_data = [
                value
                for key, value in json_bams["CNV"].items()
                if sample_id.upper() in key.upper()
            ]

        # NO BAM FOUND
        if len(sample_data) == 0:
            messages.add_message(
                request,
                messages.ERROR,
                mark_safe(
                    """Sample {} is not found in DNAnexus, either it is\
                    not available, the sample name is incorrect\
                    or some other error. <br/>Please contact\
                    the Bioinformatics team if you believe the sample\
                    should be available.""".format(
                        entered_sample_id
                    )
                ),
                extra_tags="alert-danger",
            )
            context_dict["error"] = True
            logger.error(
                (
                    re.sub(
                        r"\s+",
                        " ",
                        """Sample {} not found in JSON. Either sample
                name mistyped or an error in finding the BAMs for the
                sample, possibly missing index.""".format(
                            entered_sample_id
                        ),
                    )
                )
            )

            return render(
                request, "DNAnexus_to_igv/nexus_search.html", context_dict
            )

        flat_data = [x for xs in sample_data for x in xs]

        logger.info(f"{len(flat_data)} sample found")

        if len(flat_data) == 1:
            # ONLY ONE SAMPLE FOUND
            sample_dict = flat_data[0]

            file_url = get_dx_urls(
                sample_dict["project_id"],
                sample_dict["file_id"],
                sample_dict["file_name"],
            )
            idx_url = get_dx_urls(
                sample_dict["project_id"],
                sample_dict["idx_id"],
                sample_dict["idx_name"],
            )

            if file_url.get("error", False) or idx_url.get("error", False):
                # get the error returned
                file_error = file_url.get("error", False)
                idx_error = idx_url.get("error", False)

                # error generating urls, display message
                messages.add_message(
                    request,
                    messages.ERROR,
                    mark_safe(
                        "Error generating download URLs for sample "
                        f"{entered_sample_id}.<br/>Please contact the bioinformatics "
                        f"team for help.<br/>File Error Message: {file_error}"
                        f"<br/>Index Error Message: {idx_error}"
                    ),
                    extra_tags="alert-danger",
                )
                context_dict["error"] = True

                logger.error(
                    f"Error generating url for sample {entered_sample_id} "
                    f"{sample_dict}"
                )

                return render(
                    request, "DNAnexus_to_igv/nexus_search.html", context_dict
                )

            context_dict["file_url"] = file_url["url"]
            context_dict["idx_url"] = idx_url["url"]
            context_dict["sample_id"] = sample_id
            context_dict["file_id"] = sample_dict["file_id"]
            context_dict["file_name"] = sample_dict["file_name"]
            context_dict["project_name"] = sample_dict["project_name"]
            context_dict["file_path"] = sample_dict["file_path"]
            context_dict["file_archival_state"] = sample_dict[
                "file_archival_state"
            ]
            context_dict["idx_archival_state"] = sample_dict[
                "idx_archival_state"
            ]

            return render(
                request, "DNAnexus_to_igv/nexus_search.html", context_dict
            )
        else:
            # MULTIPLE BAMS FOUND

            context_dict["sample_id"] = sample_id

            bam_list = []

            for bam in flat_data:
                # can be mix of lists and nested lists
                if "dev" in bam["project_name"].lower():
                    # if dev data project add development after path
                    path = f"{bam['file_path']} - DEVELOPMENT"
                else:
                    path = bam["file_path"]

                bam_list.append(
                    {
                        "file_name": bam["file_name"],
                        "idx_name": bam["idx_name"],
                        "project_name": bam["project_name"],
                        "project_id": bam["project_id"],
                        "file_path": path,
                        "idx_id": bam["idx_id"],
                        "file_id": bam["file_id"],
                        "file_archival_state": bam["file_archival_state"],
                        "idx_archival_state": bam["idx_archival_state"],
                    }
                )

            paginator = Paginator(bam_list, PAGINATION)

            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)

            context_dict["bam_list"] = page_obj
            context_dict["file_no"] = len(bam_list)
            context_dict["sample_type"] = request.POST["sample_type"]

            return render(
                request, "DNAnexus_to_igv/nexus_search.html", context_dict
            )
    else:
        # This is for Pagination e.g. going to Page 2, 3 ...
        context_dict = {}
        context_dict["search_form"] = SearchForm()
        context_dict["url_form"] = UrlForm()
        context_dict["desk"] = GRID_SERVICE_DESK

        try:
            # load in json with all bams and dx attributes needed to
            # search and generate dx download links
            # if json is not present it will raise IOError
            json_path = Path(__file__).parent.absolute()
            json_file = f"{json_path}/jsons/dx_002_bams.json"
            logger.info(f"JSON FILE PATH: {json_file}")

            with open(json_file) as json_file:
                json_bams = json.load(json_file)

        except IOError as IOe:
            messages.add_message(
                request,
                messages.ERROR,
                """JSON file containing samples not found.\
                Please contact the bioinformatics team""",
            )
            context_dict["error"] = True
            logger.error(IOe)

            return render(
                request, "DNAnexus_to_igv/nexus_search.html", context_dict
            )

        sample_id = request.GET["sample_id"]
        if request.GET["sample_type"] == "BAM":
            sample_data = [
                value
                for key, value in json_bams["BAM"].items()
                if sample_id.upper() in key.upper()
            ]
        else:
            # CNV handling
            sample_data = [
                value
                for key, value in json_bams["CNV"].items()
                if sample_id.upper() in key.upper()
            ]

        flat_data = [x for xs in sample_data for x in xs]

        bam_list = []

        for bam in flat_data:
            # can be mix of lists and nested lists
            if "dev" in bam["project_name"].lower():
                # if dev data project add development after path
                path = f"{bam['file_path']} - DEVELOPMENT"
            else:
                path = bam["file_path"]

            bam_list.append(
                {
                    "file_name": bam["file_name"],
                    "idx_name": bam["idx_name"],
                    "project_name": bam["project_name"],
                    "project_id": bam["project_id"],
                    "file_path": path,
                    "idx_id": bam["idx_id"],
                    "file_id": bam["file_id"],
                    "file_archival_state": bam["file_archival_state"],
                    "idx_archival_state": bam["idx_archival_state"],
                }
            )

        paginator = Paginator(bam_list, PAGINATION)

        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context_dict["bam_list"] = page_obj
        context_dict["file_no"] = len(bam_list)
        context_dict["sample_type"] = request.GET["sample_type"]
        context_dict["sample_id"] = sample_id

        return render(
            request, "DNAnexus_to_igv/nexus_search.html", context_dict
        )


@login_required()
def select(request):
    """
    When a single sample is selected from a multiple sample list
    """

    json_path = Path(__file__).parent.absolute()
    JSON_FILE_PATH = f"{json_path}/jsons/dx_002_bams.json"

    with open(JSON_FILE_PATH) as f:
        json_bams = json.load(f)

    context_dict = {}
    context_dict["search_form"] = SearchForm()
    context_dict["url_form"] = UrlForm()

    context_dict["desk"] = GRID_SERVICE_DESK

    sample_type = request.POST["sample_type"]
    sample_id = request.POST["sample_id"]
    selected_file_id = request.POST["selected_file_id"]

    if sample_type == "BAM":
        sample_data = [
            value
            for key, value in json_bams["BAM"].items()
            if sample_id.upper() in key.upper()
        ]
    else:
        # CNV handling
        sample_data = [
            value
            for key, value in json_bams["CNV"].items()
            if sample_id.upper() in key.upper()
        ]

    flat_data: list[dict] = [x for xs in sample_data for x in xs]

    selected_sample: list[dict] = [
        v for v in flat_data if selected_file_id == v["file_id"]
    ]

    sample_dict = selected_sample[0]

    file_url = get_dx_urls(
        sample_dict["project_id"],
        sample_dict["file_id"],
        sample_dict["file_name"],
    )
    idx_url = get_dx_urls(
        sample_dict["project_id"],
        sample_dict["idx_id"],
        sample_dict["idx_name"],
    )

    if file_url.get("error", False) or idx_url.get("error", False):
        file_error = file_url.get("error", False)
        idx_error = idx_url.get("error", False)
        # error generating urls, display message
        messages.add_message(
            request,
            messages.ERROR,
            mark_safe(
                "Error generating download URLs for sample "
                f"{sample_id}.<br/>Please contact the bioinformatics "
                f"team for help.<br/>File Error Message: {file_error}"
                f"<br/>Index Error Message: {idx_error}"
            ),
        )
        context_dict["error"] = True

        logger.error(
            f"Error generating url for sample {selected_file_id} "
            f"{sample_type} {sample_dict}"
        )

        return render(
            request, "DNAnexus_to_igv/nexus_search.html", context_dict
        )

    context_dict["sample_id"] = sample_id
    context_dict["file_name"] = sample_dict["file_name"]
    context_dict["project_name"] = sample_dict["project_name"]
    context_dict["file_url"] = file_url["url"]
    context_dict["idx_url"] = idx_url["url"]
    context_dict["file_path"] = sample_dict["file_path"]
    context_dict["file_id"] = sample_dict["file_id"]
    context_dict["idx_id"] = sample_dict["idx_id"]
    context_dict["file_archival_state"] = sample_dict["file_archival_state"]
    context_dict["idx_archival_state"] = sample_dict["idx_archival_state"]

    return render(request, "DNAnexus_to_igv/nexus_search.html", context_dict)


@login_required()
def view(request):
    """
    Viewing a single sample on IGV
    """
    context_dict = {}
    context_dict["desk"] = GRID_SERVICE_DESK

    if request.POST["action"] == "igv_37":
        context_dict["reference"] = "hg19"
        context_dict["fasta"] = FASTA_37
        context_dict["fasta_idx"] = FASTA_IDX_37
        context_dict["cytoband"] = CYTOBAND_37
        context_dict["refseq"] = REFSEQ_37
        context_dict["refindex"] = REFSEQ_INDEX_37
    else:
        context_dict["reference"] = "hg38"
        context_dict["fasta"] = FASTA_38
        context_dict["fasta_idx"] = FASTA_IDX_38
        context_dict["cytoband"] = CYTOBAND_38
        context_dict["refseq"] = REFSEQ_38
        context_dict["refindex"] = REFSEQ_INDEX_38

    context_dict["genomes"] = GENOMES

    sample = request.POST["file_name"]
    bam_url = request.POST["file_url"]
    idx_url = request.POST["idx_url"]

    bam_url = str(bam_url).strip()
    idx_url = str(idx_url).strip()

    context_dict["file_name"] = sample.split(".")[0]
    context_dict["file_url"] = bam_url
    context_dict["idx_url"] = idx_url
    context_dict["file_id"] = request.POST["file_id"]

    return render(request, "DNAnexus_to_igv/nexus_igv.html", context_dict)


@login_required()
def link(request):
    """
    When a direct DNANexus link is entered
    """

    context_dict = {}
    context_dict["desk"] = GRID_SERVICE_DESK

    form = UrlForm(request.POST)
    file_url = request.POST["file_url"]
    idx_url = request.POST["index_url"]

    if form.is_valid():
        pass
    else:
        messages.add_message(
            request,
            messages.ERROR,
            """An error has occured loading IGV from the\
                provided URLs. Please check URLs are correct\
                and have been pasted in the correct fields.
                URLs used:
                File: {file_url}
                Index: {idx_url}""".format(
                file_url=file_url, idx_url=idx_url
            ),
        )
        context_dict["error"] = True

        logger.error(
            "Error loading IGV from pasted urls, most likely pasted "
            f"in wrong fields. BAM URL: {file_url}. Index URL: "
            f"{idx_url}"
        )

        return render(
            request, "DNAnexus_to_igv/nexus_search.html", context_dict
        )

    context_dict["file_name"] = "DIRECT URL"
    context_dict["file_id"] = "DIRECT URL"
    context_dict["file_url"] = file_url
    context_dict["idx_url"] = idx_url

    # check for reference by button name pressed
    if request.POST["action"] == "form_37":
        context_dict["reference"] = "hg19"
        context_dict["fasta"] = FASTA_37
        context_dict["fasta_idx"] = FASTA_IDX_37
        context_dict["cytoband"] = CYTOBAND_37
        context_dict["refseq"] = REFSEQ_37
        context_dict["refindex"] = REFSEQ_INDEX_37
    else:
        context_dict["reference"] = "hg38"
        context_dict["fasta"] = FASTA_38
        context_dict["fasta_idx"] = FASTA_IDX_38
        context_dict["cytoband"] = CYTOBAND_38
        context_dict["refseq"] = REFSEQ_38
        context_dict["refindex"] = REFSEQ_INDEX_38

    return render(request, "DNAnexus_to_igv/nexus_igv.html", context_dict)
