import django
import os
import sys
import MySQLdb

sys.path.append("../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_example.settings")

django.setup()

import genetics_ark.models as Models


def get_hgmd_annotation(db, chrom, pos, ref, alt):
    """ Returns hgmd annotation given variant data """

    query = 'SELECT info FROM hgmd_hg19_vcf WHERE chrom="{}" AND pos={} AND ref="{}" AND alt="{}"'.format(
        chrom, pos, ref, alt
    )

    cur = db.cursor()
    cur.execute(query)
    result = cur.fetchall()

    if result:
        # fetchall returns tuple of tuples
        info_fields = result[0][0].split(";")
        data = {field.split("=")[0]: field.split("=")[1] for field in info_fields}

        if data["CLASS"] and data["MUT"] == "ALT":
            return data["CLASS"]

    return

def connect_hgmd():
    """ Connect to local hgmd pro db, returns db """
    
    db = MySQLdb.connect(
        db = "hgmd_pro",
        host = "sql01",
        user = "ga_ro",
        passwd = "readonly"
    )

    return db


def get_clinvar_annotation():
    pass


def main(db = None, **variant_data):
    """
    Gather annotations from hgmd and clinvar (eventually) and returns them
    """

    if not db:
        db = connect_hgmd()
        
    hgmd_annotation = get_hgmd_annotation(
        db, 
        variant_data["chr"],
        variant_data["pos"],
        variant_data["ref"],
        variant_data["alt"]
    )

    get_clinvar_annotation()

    return hgmd_annotation



if __name__ == "__main__":
    """ Running the script on its own will add HGMD annotations to every variant in genetics ark """

    variants = Models.Variant.objects.all()

    hgmd_db = connect_hgmd()

    for variant in variants:
        chrom = str(variant.chrom)
        pos = int(variant.pos)
        ref = str(variant.ref)
        alt = str(variant.alt)

        print(chrom, pos, ref, alt)

        if not variant.hgmd:
            annotation = main(db = hgmd_db, chr = chrom, pos = pos, ref = ref, alt = alt)

            if annotation:
                print(annotation)
                variant.hgmd = annotation
                variant.save()
            else:
                print("No HGMD annotation")
        else:
            print("Already has HGMD annotation")
