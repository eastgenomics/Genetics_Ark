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

def main(gene, primer_start_37, primer_end_37, primer_start_38, primer_end_38):
    snp_date = datetime.datetime.now().strftime("%Y-%m-%d")
    snp_info = []

    for ref in ["37", "38"]:
        total_snps = gnomAD_queries.snp_check_query(gene, ref)

        if total_snps:
            for snp in total_snps:
                if ref == "37":
                    if primer_start_37 <= snp['pos'] <= primer_end_37:
                        snp_pos = snp['pos'] - primer_start_37
                        gnomad_link = "{}?dataset=gnomad_r2_1".format(snp['variant_id'])
                        snp_info.append("+{}, {}".format(snp_pos, gnomad_link))
                elif ref == "38":
                    if primer_start_38 <= snp['pos'] <= primer_end_38:
                        snp_pos = snp['pos'] - primer_start_38
                        gnomad_link = "{}?dataset=gnomad_r3".format(snp['variant_id'])
                        snp_info.append("+{}, {}".format(snp_pos, gnomad_link))

    if snp_info:
        snp_status = 2
    else:
        snp_status = 1

    return snp_status, snp_date, snp_info

if __name__ == "__main__":
    primers = Models.PrimerDetails.objects.all()

    for primer in primers:
        print(primer)
        current_snp_status = primer.snp_status
        current_snp_info = primer.snp_info
        
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

        modifications_detected = False
        new_snps = set(current_snp_info)

        for new_snp in new_snp_info:
            if current_snp_status == 0:
                new_snps.add(new_snp)
            else:
                if new_snp not in current_snp_info:
                    modifications_detected = True
                    new_snps.add(new_snp)

        if new_snps:
            primer.snp_status = "2"
        else:
            new_snps = ""
            primer.snp_status = "1"

        primer.snp_info = new_snps
        primer.snp_date = datetime.datetime.now()
        primer.save()

        time.sleep(0.0001)
