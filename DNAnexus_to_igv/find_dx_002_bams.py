"""
Searches DNAnexus cloud platform for all available 002 projects, and
creates a .json output file containing all samples with available BAMs,
along with required attributes to generate dx download links.

Must be reguarly run (i.e. via cron) to keep up to date with new
sequencing runs.
Also need to ensure the output json is in the DNAnexus_to_igv dir.

Jethro Rainford 080620
"""
import itertools
import json
import os
import re
import subprocess
import sys

import datetime as date
import dxpy as dx

from collections import defaultdict
from operator import itemgetter

# token for DNAnexus authentication
sys.path.insert(0, "../")
from ga_core.config import AUTH_TOKEN


def get_002_projects():
    """
    Get list of all 002 sequencing projects on DNAnexus to pull bams from

    Args: None

    Returns:
        - project_002_list (list): list of all 002 project names
    """
    projects = dx.search.find_projects(name="002*", name_mode="glob")
    project_002_list = [x["id"] for x in projects]
    print("Total 002 projects found:", len(project_002_list))

    return project_002_list


def find_dx_bams(project_002_list):
    """
    Function to find file and index id for a bam in DNAnexus given a
    sample id.

    Args:
        - project_002_list (list): list of all 002 dx projects

    Returns: None

    Outputs:
        - dx_002_bams.json (file): contains all 002 bams, for each:

            - bam_file_id (str): file id of BAM
            - idx_file_id (str): file id of BAM index
            - bam_name (str): human name of BAM file
            - idx_name (str): human name of index file
            - project_id (str): project id containing BAM
            - project_name (str): human name of project
            - bam_path (str): dir path of bam file
    """

    # empty dict to store bams for output in
    # use defaultdict to handle add or update of keys
    dx_data = defaultdict(list)

    # empty dict to add bams to if index is missing
    missing_bam = defaultdict(list)

    for project in project_002_list:

        bam_dict = {}
        idx_dict = {}

        bams = []
        idxs = []

        bam_files = list(dx.search.find_data_objects(
            name="*bam", name_mode="glob", project=project))

        # get full info for every bam and index in all projects
        for bam in bam_files:
            obj = dx.dxfile.DXFile(dxid=bam["id"], project=project)
            info = obj.describe()
            bams.append(info)

        idx_files = list(dx.search.find_data_objects(
            name="*bam.bai", name_mode="glob", project=project))

        for idx in idx_files:
            obj = dx.dxfile.DXFile(dxid=idx["id"], project=project)
            info = obj.describe()
            idxs.append(info)

        if bams and idxs:
            # if BAM(s) and index found, should always be found

            # get just path, name and id of each bam and index
            for bam in bams:
                bam_dict[(bam["folder"], bam["name"])] = bam["id"]

            for idx in idxs:
                idx_dict[(idx["folder"], idx["name"])] = idx["id"]


            # get project name to display
            p = dx.dxproject.DXProject(project)
            project_info = p.describe()
            project_name = project_info["name"]

            # match bams to indexes on filename and dir path
            for path, bam_file in bam_dict:
                if "tmp" in path:
                    # check if bam is in CP tmp dir, pass if True
                    continue

                if idx_dict.get((path, bam_file + ".bai")):
                    # if index with matching bam file and path is found

                    if "_" in bam_file:
                        # sample named as X001000_markdup.bam
                        sample = bam_file.split("_", 1)[0].upper()
                    else:
                        # sample named without "_" i.e X00100.bam
                        sample = bam_file.split(".", 1)[0].upper()

                    # defaultdict with list for each sample
                    dx_data[sample].append({
                        "bam_file_id": bam_dict[path, bam_file],
                        "idx_file_id": idx_dict[(path, bam_file + ".bai")],
                        "project_id": project,
                        "project_name": project_name,
                        "bam_name": bam_file,
                        "idx_name": bam_file + ".bai",
                        "bam_path": path
                    })
                else:
                    # bam missing index
                    missing_bam[bam_file].append({
                        "added_to_dict": date.datetime.now()
                        .strftime("%Y-%m-%d %H:%M:%S"),
                        "project_id": project,
                        "project_name": project_name,
                        "path": path
                    })

    # write all 002 bams into output json
    with open('dx_002_bams.json', 'w') as outfile:
        json.dump(dx_data, outfile, indent=2)

    if missing_bam:
        print(missing_bam)
        with open('dx_missing_bam.json', 'w') as missing_file:
            json.dump(missing_bam, missing_file, indent=2)


if __name__ == "__main__":

    # env variable for dx authentication
    DX_SECURITY_CONTEXT = {
        "auth_token_type": "Bearer",
        "auth_token": AUTH_TOKEN
    }
    # set token to env
    dx.set_security_context(DX_SECURITY_CONTEXT)

    project_002_list = get_002_projects()

    find_dx_bams(project_002_list)
