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
  "sample_id": [
    {
      "bam_file_id": "",
      "idx_file_id": "",
      "project_id": "",
      "project_name": "",
      "bam_name": "",
      "idx_name": "",
      "bam_path": ""
    },
    {
      "bam_file_id": "",
      "idx_file_id": "",
      "project_id": "",
      "project_name": "",
      "bam_name": "",
      "idx_name": "",
      "bam_path": ""
    }
  ],
}

Jethro Rainford 080620
"""
from collections import defaultdict
import datetime as date
import json
import os
from pathlib import Path
import sys

from dotenv import dotenv_values
import dxpy as dx


def get_002_projects():
    """
    Get list of all 002 sequencing projects on DNAnexus to pull bams
    from

    Args: None

    Returns: - project_002_list (list): list of all 002 project names
    """
    projects = dx.search.find_projects(name="002*", name_mode="glob")
    project_002_list = [x["id"] for x in projects]

    # try getting project id for dev project
    dev_project = dx.search.find_projects(
        name="003_200115_ga_igv_dev_data", name_mode="glob"
    )
    dev_project = [x for x in dev_project][0]['id']

    if dev_project:
        project_002_list.append(dev_project)
    else:
        print('dev project does not appear to exist')

    print("Total 002 projects found:", len(project_002_list))

    return project_002_list


def find_dx_bams(project_002_list):
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
    dx_data = defaultdict(list)

    # empty dict to add bams to if index is missing
    missing_bam = defaultdict(list)

    for i, project in enumerate(project_002_list):
        print(f'Searching project {project} ({i + 1}/{len(project_002_list)})')

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
                bam_dict[(bam["describe"]["folder"], bam["describe"]["name"])] = bam["id"]

            for idx in idxs:
                idx_dict[(idx["describe"]["folder"], idx["describe"]["name"])] = idx["id"]

            # get project name to display
            p = dx.dxproject.DXProject(project)
            project_info = p.describe()
            project_name = project_info["name"]

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
                    # if index with matching bam file and path is found
                    idx = indexes[0]
                elif idx_dict.get((path, indexes[1])):
                    idx = indexes[0]
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

    # ensure output jsons go to /DNAnexus_to_igv/jsons dir
    jsons_dir = f'{Path(__file__).parent.absolute()}/jsons'
    outfile_bam = f'{jsons_dir}/dx_002_bams.json'
    outfile_missing = f'{jsons_dir}/dx_missing_bam.json'

    # write all 002 bams into output json
    with open(outfile_bam, 'w') as outfile:
        json.dump(dx_data, outfile, indent=2)

    if missing_bam:
        with open(outfile_missing, 'w') as missing_file:
            json.dump(missing_bam, missing_file, indent=2)


if __name__ == "__main__":

    if len(sys.argv) > 1:
        # config / env file passed as arg
        # read in to dict and don't touch env variables
        config = dotenv_values(sys.argv[-1])
        AUTH_TOKEN = config["AUTH_TOKEN"]
    else:
        # try to get auth token from env (i.e. run in docker)
        try:
            AUTH_TOKEN = os.environ["AUTH_TOKEN"]
        except NameError as e:
            raise NameError(
                'auth token could not be retrieved from environment and no .env file passed'
            )

    # env variable for dx authentication
    DX_SECURITY_CONTEXT = {
        "auth_token_type": "Bearer",
        "auth_token": AUTH_TOKEN
    }
    # set token to env
    dx.set_security_context(DX_SECURITY_CONTEXT)

    project_002_list = get_002_projects()

    find_dx_bams(project_002_list)
