""" SNP check individual primers (main web interface) or every primers (only console)

Example:
To check every primer:

cd genetics_ark_django/utils
ml django
python snp_check.py
"""

import datetime
import django
import logging
import os
import sys
import time

import gnomAD_queries

sys.path.append("../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_example.settings")

django.setup()

import primer_db.models as Models

ALLELE_FREQUENCY_THRESHOLD = 0.005


def get_snp(ref, snp, primer_start, primer_end):
    ref2gnomad = {"37": "r2_1", "38": "r3"}

    true_snps = []

    if primer_start <= snp['pos'] <= primer_end:
        for region_type in ["exome", "genome"]:
            if not snp[region_type]:
                continue

            for pop in snp[region_type]["populations"]:
                if pop["an"] == 0:
                    continue

                pop_af = pop["ac"] / pop["an"]

                if pop_af <= ALLELE_FREQUENCY_THRESHOLD and pop_af != 0:
                    snp_pos = snp['pos'] - primer_start
                    gnomad_link = "{}?dataset=gnomad_{}".format(snp['variant_id'], ref2gnomad[ref])
                    true_snps.append("+{}, {}".format(snp_pos, gnomad_link))

    return true_snps
                

def main(gene, primer_start_37, primer_end_37, primer_start_38, primer_end_38):
    snp_date = datetime.datetime.now().strftime("%Y-%m-%d")
    snp_info = []

    for ref in ["37", "38"]:
        total_snps = gnomAD_queries.snp_check_query(gene, ref)

        if total_snps:
            for snp in total_snps:
                snp_info += get_snp(ref, snp, primer_start_37, primer_end_37)
                snp_info += get_snp(ref, snp, primer_start_38, primer_end_38)

    if snp_info:
        snp_status = 2
    else:
        snp_status = 1

    return snp_status, snp_date, snp_info

if __name__ == "__main__":
    today = datetime.datetime.now().strftime("%y%m%d")
    record_file_path = "snp_checking_update/{}".format(today)

    if not os.path.exists("snp_checking_update"):
        os.mkdir("snp_checking_update")

    primers = Models.PrimerDetails.objects.all()

    with open(record_file_path, "a") as f:
        for primer in primers:
            f.write("{}:\n".format(primer))
            current_snp_status = primer.snp_status
            current_snp_info = primer.snp_info

            f.write(" - Current snps: {}\n".format(current_snp_info))

            if current_snp_info:
                current_snp_info = current_snp_info.split(";")
            else:
                current_snp_info = []

            new_status, new_snp_date, new_snp_info = main(
                primer.gene,
                primer.coordinates.start_coordinate_37,
                primer.coordinates.end_coordinate_37,
                primer.coordinates.start_coordinate_38,
                primer.coordinates.end_coordinate_38
            )

            new_snps = current_snp_info

            for new_snp in new_snp_info:
                if current_snp_status == 0:
                    new_snps.append(new_snp)
                else:
                    if new_snp not in current_snp_info:
                        new_snps.append(new_snp)

            if new_snps:
                new_snps = ";".join(set(new_snps))
                f.write(" - New snps detected: {}\n".format(new_snp_info))
                primer.snp_status = "2"
            else:
                f.write(" - No new snps\n")
                new_snps = ""
                primer.snp_status = "1"

            primer.snp_info = new_snps
            primer.snp_date = datetime.datetime.now()
            primer.save()

            time.sleep(0.0001)
