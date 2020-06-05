import itertools
import json
import os
import re
import subprocess
import sys

from operator import itemgetter

def get_002_projects():
    """
    Get list of all 002 sequencing projects on DNAnexus to pull bams from

    Args: None

    Returns:
        - project_002_list (list): list of all 002 project names 
    """

    # dx command to find 002 projects
    dx_find_projects = "dx find projects --level VIEW --name 003_200504_J*"
    
    projects_002 = subprocess.check_output(dx_find_projects, shell=True)

    # get just the project id's from returned string
    projects_002 = projects_002.replace("\n", " ").split(" ")
    project_002_list = [x for x in projects_002 if x.startswith('project-')]

    return project_002_list


def find_dx_bams(project_002_lists):
    """
    Function to find file and index id for a bam in DNAnexus given a 
    sample id.

    Args:
        - project id (str): DNAnexus project id for 002 project
        - sample_id (str): sample no. from search field
        - dx_data (list): list to append info for each bam to

    Returns:
        - dx_data (list): list containing following for each BAM found:
            - bam_file_id (str): file id of BAM
            - idx_file_id (str): file id of BAM index
            - bam_project_id (str): project id containing BAM
            - idx_project_id (str): project id containing BAM index
            - bam_name (str): human name of BAM file
            - project_name (str): human name of project
            - bam_folder (str): dir path of bam file
            - idx_folder (str): dir path of index file
    """

    for project in project_002_list:
        # dx commands to retrieve bam and bam.bai for given sample
        dx_find_bam = "dx find data --path {project} --name *.bam".format(
            project = project)

        dx_find_idx = "dx find data --path {project} --name *.bam.bai".format(
            project = project)

        bam = subprocess.check_output(dx_find_bam, shell=True)
        idx = subprocess.check_output(dx_find_idx, shell=True)

        bam_idx_list = []
        bam_dict ={}
        idx_dict = {}

        if bam and idx:
            # if BAM(s) and index found, should always be found

            # list returned as one string
            bams = bam.split("\n")[:-1]
            idxs = idx.split("\n")[:-1]
            
            # split out bam string and get required fields
            for bam in bams:
                bam = filter(None, bam.split(" "))

                path = bam[5].rsplit('/', 1)[0]
                file = bam[5].rsplit('/', 1)[1]
                file_id = bam[-1].strip("()")

                bam_dict[(path, file)] = file_id         

            # split out index string and get required fields
            for idx in idxs:
                idx = filter(None, idx.split(" "))

                path = idx[5].rsplit('/', 1)[0]
                file = idx[5].rsplit('/', 1)[1]
                file_id = idx[-1].strip("()")

                idx_dict[(path, file)] = file_id
          
            # match bams to indexes on filename and dir path
            for path, bam_file in bam_dict:
                if idx_dict[(path, bam_file+".bai")]:
                    # if index with matching bam file and path is found
                    bam_idx_list.append({
                                    "bam_file": bam_file,
                                    "bam_id": bam_dict[path, bam_file],
                                    "path": path,
                                    "idx_file": bam_file+".bai",
                                    "idx_id": idx_dict[path, bam_file+".bai"]
                                    })
            
            sys.exit()

            """Need to change for new list"""

            for bam_id, idx_id in itertools.izip(bams_list, idx_list):
                # for each pair of bam and index, get file attributes

                # dx commands to get readable file and project names
                dx_bam_name = "dx describe --json {}".format(bam_id)
                dx_idx_name = "dx describe --json {}".format(idx_id)
                dx_project_name = "dx describe --json {}".format(project_id)

                # returns a json as a string so convert back to json to select name 
                # and id's out
                bam_json = json.loads(subprocess.check_output(dx_bam_name, shell=True))
                idx_json = json.loads(subprocess.check_output(dx_idx_name, shell=True))

                project_id = bam_json["project"]
                project_json = json.loads(subprocess.check_output(dx_project_name, 
                                                                    shell=True))
                
                # get bam and project names to display
                bam_name = bam_json["name"]
                project_name = project_json["name"]

                # get bam and index project ids to check they're from same run
                bam_project_id = bam_json["project"]
                idx_project_id = idx_json["project"]

                # get dir path to display when multiple BAMs found in same project
                bam_folder = bam_json["folder"]
                idx_folder = idx_json["folder"]

                # add required data to list
                dx_data.append({
                                "bam_file_id": bam_id,
                                "idx_file_id": idx_id,
                                "bam_project_id": bam_project_id,
                                "idx_project_id": idx_project_id,
                                "bam_name": bam_name,
                                "project_name": project_name,
                                "bam_folder": bam_folder,
                                "idx_folder": idx_folder
                                })

project_002_list = get_002_projects()
print project_002_list

find_dx_bams(project_002_list)


