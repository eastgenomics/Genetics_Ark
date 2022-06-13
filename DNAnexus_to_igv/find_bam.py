"""
Searches DNAnexus cloud platform for all available 002 projects, and
creates a .json output file containing all samples with available BAMs
and another of those missing indexes, along with required attributes to
generate dx download links.

Must be reguarly run (i.e. via cron) to keep up to date with new
sequencing runs. Also need to ensure the output json is in the
DNAnexus_to_igv dir.

Creates JSONs with following structure:
{
    "BAM":
        "sample_id": [
            {
                "file_id": "",
                "idx_id": "",
                "project_id": "",
                "project_name": "",
                "file_name": "",
                "idx_name": "",
                "file_path": "",
                "idx_path": "",
                "file_archival_state": "",
                "idx_archival_state": ""
            },
            {
                "file_id": "",
                "idx_id": "",
                "project_id": "",
                "project_name": "",
                "file_name": "",
                "idx_name": "",
                "file_path": "",
                "idx_path": "",
                "file_archival_state": "",
                "idx_archival_state": ""
            }
        ],
    "CNV":
        "sample_id": [
            {
                "file_id": "",
                "idx_id": "",
                "project_id": "",
                "project_name": "",
                "file_name": "",
                "idx_name": "",
                "file_path": "",
                "idx_path": "",
                "file_archival_state": "",
                "idx_archival_state": "",
                "cnv": true
            }
        ]
}

Jethro Rainford 080620
"""

import datetime as date
import dxpy as dx
import json
import os

from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

PROJECT_CNVS = 'project-FzyfP204Z5qXBp6696jG5g10'

def get_002_projects():
    """
    Get list of all 002 sequencing projects on DNAnexus to pull bams
    from

    Args: None

    Returns: - project_002_list (list): list of all 002 project id
    """
    load_dotenv(find_dotenv())

    projects = list(dx.search.find_projects(name="002*", name_mode="glob", describe=True))
    project_002_list = [x["id"] for x in projects]
    projects_name = {x['id']: x['describe']['name'] for x in projects}

    DEV_PROJECT_NAME = os.environ["DEV_PROJECT_NAME"]

    dev_project = list(dx.search.find_projects(name=DEV_PROJECT_NAME, name_mode="glob"))

    if dev_project:
        dev_project = [x['id'] for x in dev_project]
        project_002_list.append(dev_project)
    else:
        print('DEV PROJECT DOES NOT APPEAR TO EXIST')

    print("Total 002 projects found:", len(project_002_list))

    return project_002_list, projects_name


def find_dx_bams(project_002_list, project_names):
    """
    Function to find file and index id for a bam in DNAnexus given a
    sample id.

    Args: - project_002_list (list): list of all 002 dx projects

    Returns: None

    Outputs: - dx_002_bams.json (file): contains all 002 bams, for each:

            - bam_file_id (str): file id of BAM
            - idx_file_id (str): file id of BAM index
            - bam_name (str): human name of BAM file
            - idx_name (str): human name of index file
            - project_id (str): project id containing BAM
            - project_name (str): human name of project
            - bam_path (str): dir path of bam file
    """
    # empty dict to store bams for output in use defaultdict to handle
    # add or update of keys
    dx_data = defaultdict(lambda: defaultdict(list))

    # empty dict to add bams to if index is missing
    missing_bam = defaultdict(list)

    # loop through proj to get bam file in each of them
    for index, project in enumerate(project_002_list):
        print(f'Searching {project} ({index + 1}/{len(project_002_list)})')

        bam_dict = {}
        idx_dict = {}

        bams = list(dx.search.find_data_objects(
            name="*bam", name_mode="glob", project=project, describe=True))


        idxs = list(dx.search.find_data_objects(
            name="*bam.bai", name_mode="glob", project=project, describe=True))

        if bams and idxs:
            # if BAM(s) and index found, should always be found

            # add path, name and id of each bam and index to dicts
            for bam in bams:
                bam_dict[(bam["describe"]["folder"], bam["describe"]["name"])] = {
                    'id': bam["id"],
                    'archivalState': bam['describe']['archivalState']
                    }

            for idx in idxs:
                idx_dict[(idx["describe"]["folder"], idx["describe"]["name"])] = {
                    'id': idx["id"],
                    'archivalState': bam['describe']['archivalState']
                    }

            # get project name to display
            project_name = project_names[project]

            # match bams to indexes on filename and dir path
            for path, bam_file in bam_dict.keys():
                if "tmp" in path:
                    # check if bam is in CP tmp dir, pass if True
                    continue

                # index either can be .bam.bai or just .bai for old
                # samples, get names for both to check
                indexes = []
                indexes.append(f"{bam_file}.bai")
                indexes.append(f"{bam_file.strip('.bam')}.bai")

                if idx_dict.get((path, indexes[0])):
                    idx = indexes[0]
                elif idx_dict.get((path, indexes[1])):
                    idx = indexes[1]
                else:
                    # bam missing index
                    missing_bam[bam_file].append({
                        "added_to_dict": date.datetime.now()
                        .strftime("%Y-%m-%d %H:%M:%S"),
                        "project_id": project,
                        "project_name": project_name,
                        "path": path
                    })
                    continue

                if "_" in bam_file:
                    # sample named as X001000_markdup.bam
                    sample = bam_file.split("_", 1)[0].upper()
                else:
                    # sample named without "_" i.e X00100.bam
                    sample = bam_file.split(".", 1)[0].upper()

                bam_id = bam_dict[path, bam_file]['id']
                bam_archival_state = bam_dict[path, bam_file]['archivalState']
                
                idx_id = idx_dict[(path, idx)]['id']
                idx_archival_state = bam_dict[path, bam_file]['archivalState']

                # defaultdict with list for each sample
                dx_data['BAM'][sample].append({
                    "file_id": bam_id,
                    "idx_id": idx_id,
                    "project_id": project,
                    "project_name": project_name,
                    "file_name": bam_file,
                    "idx_name": idx,
                    "file_path": path,
                    "file_archival_state": bam_archival_state,
                    "idx_archival_state": idx_archival_state
                })
    
    find_cnvs(dx_data)

    # ensure output jsons go to /DNAnexus_to_igv/jsons dir
    output_dir = f'{Path(__file__).parent.absolute()}/jsons'
    print(f'JSON saved to: {output_dir}')
    
    outfile_bam = f'{output_dir}/dx_002_bams.json'
    outfile_missing = f'{output_dir}/dx_missing_bam.json'

    # write all 002 bams into output json
    with open(outfile_bam, 'w') as outfile:
        json.dump(dx_data, outfile, indent=2)

    if missing_bam:
        with open(outfile_missing, 'w') as missing_file:
            json.dump(missing_bam, missing_file, indent=2)

def find_cnvs(data_dict):

    print('Searching for CNVs')

    project_name = dx.DXProject(PROJECT_CNVS).describe()['name']

    for file in list(
        dx.find_data_objects(
            project=PROJECT_CNVS, 
            name='.*_copy_ratios.gcnv.bed.gz\Z', 
            name_mode='regexp', 
            describe=True)):
        
        cnv_name = file['describe']['name']
        cnv_path = file['describe']['folder']
        cnv_id = file['id']
        cnv_archival_status = file['describe']['archivalState']


        cnv_index = list(dx.find_data_objects(
            project=PROJECT_CNVS,
            name=f'{cnv_name}.tbi',
            name_mode='regexp',
            folder=cnv_path,
            describe=True,
            limit=1
        ))

        cnv_dict = {
            'file_name':cnv_name,
            'file_id':cnv_id,
            'file_path':cnv_path,
            'file_archival_state':cnv_archival_status,
            'project_id':PROJECT_CNVS,
            'project_name':project_name,
            'CNV':True
        }

        if cnv_index:
            cnv_dict['idx_name'] = cnv_index[0]['describe']['name']
            cnv_dict['idx_id'] = cnv_index[0]['id']
            cnv_dict['idx_path'] = cnv_index[0]['describe']['folder']
            cnv_dict['idx_archival_state'] = cnv_index[0]['describe']['archivalState']
        else:
            cnv_dict['idx_name'] = None
            cnv_dict['idx_id'] = None
            cnv_dict['idx_path'] = None
            cnv_dict['idx_archival_state'] = None

        data_dict['CNV'][cnv_name.rstrip('_copy_ratios.gcnv.bed.gz')].append(cnv_dict)
    
    print('Searching for CNVs End')