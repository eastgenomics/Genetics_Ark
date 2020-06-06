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
    #dx_find_projects = "dx find projects --level VIEW --name 003_200504_J*"
    dx_find_projects = "dx find projects --level VIEW --name 002*"
    
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
    dx_data = {}
    dx_data['bam'] = []

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

        print project

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

                # add all bams to dict
                bam_dict[(path, file)] = file_id         

            # split out index string and get required fields
            for idx in idxs:
                idx = filter(None, idx.split(" "))

                path = idx[5].rsplit('/', 1)[0]
                file = idx[5].rsplit('/', 1)[1]
                file_id = idx[-1].strip("()")

                # add all indexes to dict
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

            # get project name to display
            dx_project_name = "dx describe --json {}".format(project)

            # returns a json as a string so convert back to json to select name 
            project_json = json.loads(subprocess.check_output(dx_project_name, 
                                                                shell=True))
            project_name = project_json["name"]

            for bam in bam_idx_list:
                # for each pair of bam and index, add to dx_data

                dx_data["bam"].append({
                                "bam_file_id": bam["bam_id"],
                                "idx_file_id": bam["idx_id"],
                                "project_id": project,
                                "project_name": project_name,
                                "bam_name": bam["bam_file"],
                                "idx_name": bam["idx_file"],
                                "bam_path": bam["path"]
                                })

    # write all 002 bams into output json
    with open('dx_002_bams.json', 'w') as outfile:
        json.dump(dx_data, outfile, indent=2)

if __name__ == "__main__":
    project_002_list = get_002_projects()

    find_dx_bams(project_002_list)


