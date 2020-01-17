from collections import defaultdict
import django
import os
import re
import sys
import subprocess

import gnomAD_queries

sys.path.append("../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_example.settings")

django.setup()

import primer_db.models as Models

SMALT_FASTA = "primers_smalt.fasta"
REF_37 = "/mnt/storage/data/refs/homo_sapiens/GRCh37/Homo_sapiens_assembly37"
REF_38 = "/mnt/storage/data/refs/homo_sapiens/GRCh38/Homo_sapiens_assembly38"


def multiple_mapping_check(*primers, temp_fasta = SMALT_FASTA):
    """ Given primers model objects, align and add comments """

    with open(temp_fasta, "w") as f:
        for primer in primers:
            if "tgtaaaacgacggccagt" in primer.sequence:
                sequence = primer.sequence.replace("tgtaaaacgacggccagt", "")
            else:
                sequence = primer.sequence

            f.write(">{}\n{}\n".format(primer.name, sequence))

    success = main(temp_fasta)

    if success:
        print("SUCCESS")
        return True
    else:
        print("FAILED")
        return False


def run_smalt(cmd):
    print("MAPPING...")
    print(cmd)
    process = subprocess.run(cmd, shell = True, stdout = subprocess.PIPE, stderr = subprocess.PIPE)

    if process.returncode != 0:
        print("SMALT issue: \"{}\"".format(process.stderr.decode("ascii").strip()))
        return False
    
    smalt_output = process.stdout.decode("ascii").strip()
    smalt_output = [line for line in smalt_output.split("\n") if not line.startswith("@")]

    # for line in smalt_output:
    #     print(line.split("\t"))

    print("PARSING SMALT OUTPUT...")

    kept_primers = {}

    for line in smalt_output:
        line = line.split('\t')
        name = line[0]
        primer = Models.PrimerDetails.objects.get(name = name)
        smalt_chrom = line[2]
        smalt_seq = line[9]
        smalt_nm_tag = line[11]
        smalt_as_tag = line[12]
        smalt_cigar = line[5]

        if not smalt_as_tag.startswith("AS"):
            print("AS tag not at expected position")
            return False

        if not smalt_nm_tag.startswith("NM"):
            print("NM tag not at expected position")
            return False

        # get just primers on correct chromosome
        if primer.coordinates.chrom_no == smalt_chrom:
            length_minus_alignscore = len(smalt_seq) - int(smalt_as_tag.split(':')[2])

            if re.search(r"[^M0-9]", smalt_cigar):
                parsing_cigar = []
                cigar_op = ""

                for char in smalt_cigar:
                    if not char.isdigit():
                        parsing_cigar.append((int(cigar_op), char))
                        cigar_op = ""
                    else:
                        cigar_op += char

                if parsing_cigar[-1][1] not in ["M", "="]:
                    continue
                else:
                    if parsing_cigar[-1][0] <= 15:
                        continue

            if length_minus_alignscore <= 5:
                kept_primers.setdefault(primer, []).append(line)

    return kept_primers


def check_nb_mapping(primer2mappings):
    comment = "Multiple mapping detected, check before use"

    for primer, mappings in primer2mappings.items():
        if len(mappings) >= 3:
            if primer.pairs_id:
                paired_primers = Models.PrimerDetails.objects.filter(pairs_id = primer.pairs_id)

                if len(paired_primers) != 2:
                    print("{} have this pair id {}".format(len(paired_primers), primer.pairs_id))
                    return False
                else:
                    primers_to_comment = paired_primers

            else:
                primers_to_comment = primer

            for primer_to_comment in primers_to_comment:
                primer_to_update = Models.PrimerDetails.objects.filter(name = primer_to_comment.name)

                if primer_to_update[0].comments:
                    if comment not in primer_to_update[0].comments:
                        new_comment = "{}\n{}".format(primer_to_update[0].comments, comment)
                    else:
                        continue
                else:
                    new_comment = comment

                # primer_to_update.update(**{"comments": new_comment})

    return True


def main(temp_fasta):
    all_mappings = []

    cmd_37 = "smalt map -d -1 -m 15 {} {}".format(REF_37, temp_fasta)
    cmd_38 = "smalt map -d -1 -m 15 {} {}".format(REF_38, temp_fasta)

    for cmd in [cmd_37, cmd_38]:
        all_mappings.append(run_smalt(cmd))

    if all(all_mappings):
        print("CHECKING NB MAPPINGS PER PRIMER...")

        for mapping_dict in all_mappings:
            success = check_nb_mapping(mapping_dict)

            if not success:
                return False
    else:
        print("SMALT issue")
        return False

    return True



if __name__ == "__main__":
    primers = Models.PrimerDetails.objects.all()
    multiple_mapping_check(*primers)