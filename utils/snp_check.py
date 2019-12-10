import datetime
import django
import os
import sys

import gnomAD_queries

sys.path.append("../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "genetics_ark_django.settings")

django.setup()

def main(*args):
    gene, primer_start_37, primer_end_37, primer_start_38, primer_end_38 = args
    
    snp_date = datetime.datetime.now().strftime("%Y-%m-%d")
    snp_info = []

    for ref in ["37", "38"]:
        snp_pos = []
        snp_detail = []

        total_snps = gnomAD_queries.snp_check_query(gene, ref)

        if total_snps:
            for snp in total_snps:
                if ref == "37":
                    if primer_start_37 <= snp['pos'] <= primer_end_37:
                        snp_pos.append(snp['pos'] - primer_start_37)
                        snp_detail.append("{}?dataset=gnomad_r2_1".format(snp['variant_id']))
                elif ref == "38":
                    if primer_start_38 <= snp['pos'] <= primer_end_38:
                        snp_pos.append(snp['pos'] - primer_start_38)
                        snp_detail.append("{}?dataset=gnomad_r3".format(snp['variant_id']))

    if snp_detail:
        for i, snp in enumerate(snp_detail):
            snp_info.append("+{}, {}".format(
                snp_pos[i], snp))

        snp_status = 2
    else:
        snp_status = 1

    return snp_status, snp_date, snp_info

if __name__ == "__main__":
    args = sys.argv[1:]
    main(*args)