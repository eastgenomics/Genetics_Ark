""" SNP check individual primers (main web interface) or every primers (only console)

Example:
To check every primer:

cd genetics_ark_django/utils
ml django
python snp_check.py
"""

import argparse
import datetime
import django
import os
import sys
import time

import gnomAD_queries

sys.path.append("../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_example.settings")

django.setup()

import primer_db.models as Models

sys.path.append("/mnt/storage/home/kimy/projects/HGNC_api/bin/")

import hgnc_queries

ALLELE_FREQUENCY_THRESHOLD = 0.005
hgnc_dict = {}


def rescue_gene_symbol_with_HGNC(gene_symbol):
    """ Get HGNC symbol for gene symbol given if the gene symbol is not recognized in gnomAD """

    if gene_symbol not in hgnc_dict:
        new_symbol = hgnc_queries.get_new_symbol(gene_symbol, False)

        if new_symbol:
            for ref in ["37", "38"]:
                query_res = gnomAD_queries.snp_check_query(new_symbol, ref)

                if query_res:
                    hgnc_dict[gene_symbol] = new_symbol
                    return new_symbol
                
                time.sleep(0.0001)
        else:
            main_symbol = hgnc_queries.get_main_symbol(gene_symbol, False)

            if main_symbol:
                for ref in ["37", "38"]:
                    query_res = gnomAD_queries.snp_check_query(main_symbol, ref)

                    if query_res:
                        hgnc_dict[gene_symbol] = main_symbol
                        return main_symbol

                    time.sleep(0.0001)
            
            else:
                hgnc_dict[gene_symbol] = None
        
    else:
        new_gene = hgnc_dict[gene_symbol]
        return new_gene

    return None
    

def get_snp(ref, snp, primer_start, primer_end):
    """ Given a snp and the coordinates of a primer, return list with position of snp on the primer + gnomAD link """

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

                if pop_af >= ALLELE_FREQUENCY_THRESHOLD and pop_af != 0:
                    snp_pos = snp['pos'] - primer_start
                    gnomad_link = "{}?dataset=gnomad_{}".format(snp['variant_id'], ref2gnomad[ref])
                    
                    if "+{}, {}".format(snp_pos, gnomad_link) not in true_snps:
                        true_snps.append("+{}, {}".format(snp_pos, gnomad_link))

    return true_snps
                

def main(gene, primer_start_37, primer_end_37, primer_start_38, primer_end_38):
    """ Returns snp data for primer_db 

    Args:
     - gene
     - primer start 37
     -        end   37
     - primer start 38
     -        end   38

    Returns:
     - snp status
     - snp date
     - snp info
    """

    snp_date = datetime.datetime.now().strftime("%Y-%m-%d")
    snp_info = []
    ref_37 = True
    ref_38 = True

    for ref in ["37", "38"]:
        total_snps = gnomAD_queries.snp_check_query(gene, ref)

        if not total_snps:
            # gene symbol not recognized by gnomAD, try and rescue with HGNC
            new_gene = rescue_gene_symbol_with_HGNC(gene)
            
            if new_gene:
                total_snps = gnomAD_queries.snp_check_query(new_gene, ref)
                print(total_snps)

                if not total_snps:
                    # still not recognized
                    snp_info += ["Gene not recognized for {}".format(ref)]

                    if ref == "37":
                        ref_37 = False
                    elif ref == "38":
                        ref_38 = False

                    continue

                time.sleep(0.0001)
            
            else:
                # couldn't rescue gene symbol
                snp_info += ["Gene not recognized for {}".format(ref)]

                if ref == "37":
                    ref_37 = False
                elif ref == "38":
                    ref_38 = False

                continue

        for snp in total_snps:
            if ref == "37":
                snp_info += get_snp(ref, snp, primer_start_37, primer_end_37)
            elif ref == "38":
                snp_info += get_snp(ref, snp, primer_start_38, primer_end_38)

    if snp_info:
        if not ref_37 and not ref_38:
            snp_status = "4"
        elif ref_37 and ref_38:
            snp_status = "2"
        else:
            if len(snp_info) == 1:
                snp_status = "1"
            else:
                snp_status = "2"
    else:
        snp_status = "1"

    return snp_status, snp_date, snp_info



if __name__ == "__main__":
    """
    Launching the script on it's own will check every primers in the database
    You can filter using the snp status
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--status", required = False, help = "Snp status of primers to check")
    args = parser.parse_args()

    today = datetime.datetime.now().strftime("%y%m%d")
    record_file_path = "snp_checking_update/{}".format(today)

    if not os.path.exists("snp_checking_update"):
        os.mkdir("snp_checking_update")

    if args.status:
        primers = Models.PrimerDetails.objects.filter(snp_status = args.status)
    else:
        primers = Models.PrimerDetails.objects.all()

    with open(record_file_path, "a") as f:
        for i, primer in enumerate(primers):
            print(i, primer.name)
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
                if new_snps == ["Gene not recognized for 37", "Gene not recognized for 38"]:
                    f.write(" - Gene not recognized\n")
                else:
                    if len(new_snps) >= 2:
                        f.write(" - New snps detected: {}\n".format(new_snp_info))
                    else:
                        f.write(" - No new snps, gene not recognized for a ref\n")

                new_snps = ";".join(set(new_snps))
                primer.snp_status = new_status
            else:
                f.write(" - No new snps\n")
                new_snps = ""
                primer.snp_status = new_status

            primer.snp_info = new_snps
            primer.snp_date = datetime.datetime.now()
            primer.save()

            # needs it because of the timeout parameters in the gnomAD API
            time.sleep(0.0001)
