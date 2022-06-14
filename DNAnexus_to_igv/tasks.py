# task to update bam / cnv json file
from .find_bam import get_002_projects, find_dx_bams

def update_json():
    proj_list, proj_name = get_002_projects()
    find_dx_bams(proj_list, proj_name)

update_json()
        