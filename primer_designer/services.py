import os
import subprocess
from zipfile import ZipFile
from pathlib import Path

PRIMER_PATH = "/home/primer_designer/bin"


def call_subprocess(output_directory: str, regions: str, output_name) -> bool:
    """
    Service ran by Django-Q
    Function to format input command (primer designer)
    and call subprocess to run primer3
    """

    for region in regions:
        cmd = _format_region(region, output_name)

        primer_cmd = f"python3 {PRIMER_PATH}/primer_designer_region.py {cmd}"

        print(primer_cmd)

        # call subprocess to run primer3
        call = subprocess.run(
            primer_cmd.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if call.returncode != 0:
            print(call.stdout)
            return False, call.stdout

    # zip the PDFs in output dir
    with ZipFile(f"{output_directory}.zip", "w") as zfile:
        for pdf in os.listdir(output_directory):
            zfile.write(f"{output_directory}/{pdf}", Path(pdf).name)

    return True, {}


def _format_region(region: str, dir: str) -> str:
    """
    Format region from input form as command (str) for primer designer

    Args:
        region (str): region passed from Input Form
        dir (str): output directory for primer designs
    Returns: cmd (str): formatted str of cmd for primer designer
    """
    region = region.replace('\t', ' ')  # deal with tab-delimited inputs

    if region.count(":") > 1:
        # format for fusion design, will be in format
        # chr:pos:side:strand chr:pos:side:strand build 'fusion'
        primer_namer, b1, b2, build = region.split()
        cmd = f'--fusion --b1 {b1} --b2 {b2} --{build} -d {dir} -o {primer_namer}_{b1.replace(":", "_")}_{b2.replace(":", "_")}_{build}'
    else:
        # either position or range design
        if "-" in region:
            # range design, will be in format chr:pos1-pos2 build
            primer_name, region, build = region.split()
            chr, pos = region.split(":")
            pos1, pos2 = pos.split("-")

            cmd = f"-c {chr} -r {pos1} {pos2} --{build} -d {dir} -o {primer_name}_{chr}_{pos1}_{pos2}_{build}"
        else:
            # normal position design, in format chr:pos build
            primer_name, region, build = region.split()
            chr, pos = region.split(":")

            cmd = f"-c {chr} -p {pos} --{build} -d {dir} -o {primer_name}_{chr}_{pos}_{build}"

    return cmd
