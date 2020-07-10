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

from collections import defaultdict
from operator import itemgetter

# token for DNAnexus log in
sys.path.insert(0, "../")
from django_example.config import AUTH_TOKEN


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

    for project in project_002_list:
        # dx commands to retrieve bam and bam.bai for given sample
        dx_find_bam = "dx find data --path {project} --name *.bam".format(
            project=project)
        dx_find_idx = "dx find data --path {project} --name *.bam.bai".format(
            project=project)

        bam = subprocess.check_output(dx_find_bam, shell=True)
        idx = subprocess.check_output(dx_find_idx, shell=True)

        bam_dict = {}
        idx_dict = {}

        if bam and idx:
            # if BAM(s) and index found, should always be found

            # list returned as one string
            bams = bam.split("\n")[:-1]
            idxs = idx.split("\n")[:-1]
            
            for bam in bams:
                # split out bam string and get required fields
                bam = filter(None, bam.split(" "))

                path = bam[5].rsplit('/', 1)[0]
                file = bam[5].rsplit('/', 1)[1]
                file_id = bam[-1].strip("()")

                # add all bams to dict
                bam_dict[(path, file)] = file_id         
            
            for idx in idxs:
                # split out index string and get required fields
                idx = filter(None, idx.split(" "))

                path = idx[5].rsplit('/', 1)[0]
                file = idx[5].rsplit('/', 1)[1]
                file_id = idx[-1].strip("()")

                # add all indexes to dict
                idx_dict[(path, file)] = file_id

            # get project name to display
            dx_project_name = "dx describe --json {project}".format(project=project)

            # returns a json as a string so convert back to json to select name 
            project_json = json.loads(subprocess.check_output(dx_project_name, 
                                                                shell=True))
            project_name = project_json["name"]

            # match bams to indexes on filename and dir path
            for path, bam_file in bam_dict:
                if idx_dict[(path, bam_file+".bai")]:
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
                            "idx_file_id": idx_dict[(path, bam_file+".bai")],
                            "project_id": project,
                            "project_name": project_name,
                            "bam_name": bam_file,
                            "idx_name": bam_file+".bai",
                            "bam_path": path
                            })

    # write all 002 bams into output json
    with open('dx_002_bams.json', 'w') as outfile:
        json.dump(dx_data, outfile, indent=2)

if __name__ == "__main__":

    # log in to DNAnexus to do queries 
    login = "dx login --token {} --noprojects".format(AUTH_TOKEN)
    subprocess.check_output(login, shell=True)
    
    project_002_list = get_002_projects()

    find_dx_bams(project_002_list)


