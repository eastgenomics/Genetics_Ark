import os
import subprocess
from zipfile import ZipFile
from pathlib import Path


def call_subprocess(output_directory: str, regions: str, output_name) -> bool:
    """
    Service ran by Django-Q
    Function to format input command (primer designer)
    and call subprocess to run primer3
    """

    for region in regions:
        cmd = format_region(region, output_name)
        genome_build = cmd.split(' ')[-1].lstrip('--')

        primer_path = '/home/primer_designer/bin'

        if genome_build == 'grch37':
            primer_cmd = 'python3 {}/primer_designer_region.py {}'.format(
                primer_path, cmd)
        else:
            primer_cmd = 'python3 {}/primer_designer_region.py {}'.format(
                primer_path, cmd
            )
        print(primer_cmd)

        # call subprocess to run primer3
        call = subprocess.run(
            primer_cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True)

        if call.returncode != 0:
            print(call.stdout)
            return False, call.stdout

    # zip the PDFs in output dir
    with ZipFile(f'{output_directory}.zip', 'w') as zfile:
        for pdf in os.listdir(output_directory):
            zfile.write(
                f'{output_directory}/{pdf}', Path(pdf).name)

    return True, {}


def format_region(region, dir):
    """
    Format region from input form as command (str) for primer designer

    Args: region (str): region passed from Input Form
    Returns: cmd (str): formatted str of cmd for primer designer
    """
    if region.count(':') > 1:
        # format for fusion design, will be in format
        # chr:pos:side:strand chr:pos:side:strand build 'fusion'
        args = region.split()
        cmd = f'--fusion --b1 {args[0]} --b2 {args[1]} --{args[2]} -d {dir}'
    else:
        # either position or range design
        if '-' in region:
            # range design, will be in format chr:pos1-pos2 build
            region, build = region.split()
            chr, pos = region.split(':')
            pos1, pos2 = pos.split('-')

            cmd = f'-c {chr} -r {pos1} {pos2} --{build} -d {dir}'
        else:
            # normal position design, in format chr:pos build
            region, build = region.split()
            chr, pos = region.split(':')

            cmd = f'-c {chr} -p {pos} --{build} -d {dir}'

    return cmd
