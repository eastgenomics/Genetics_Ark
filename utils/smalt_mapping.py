import django
import os
import sys
import subprocess


import gnomAD_queries

sys.path.append("../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_example.settings")

django.setup()

import primer_db.models as Models


def main():

    with open(primers_file, 'w+') as primer_fasta:
        for primer in primers:
            primer_fasta.write(">{}\n{}\n".format(primer.name, primer.sequence))
        
        primer_fasta.close()

    chrom = primer.coordinates.chrom_no
    
    ref_37 = "/mnt/storage/data/refs/homo_sapiens/GRCh37/Homo_sapiens_assembly37"
    ref_38 = "/mnt/storage/data/refs/homo_sapiens/GRCh38/Homo_sapiens_assembly38"

    cmd_37 = "smalt map -d -1 -m 15 {} {}".format(ref_37, primers_file)
    cmd_38 = "smalt map -d -1 -m 15 {} {}".format(ref_38, primers_file)

    smalt_out_37 = subprocess.run(cmd_37, shell = True, stdout = subprocess.PIPE).stdout.decode("ascii").strip()
    smalt_out_37 = [line for line in smalt_out_37.split("\n") if not line.startswith("@")]
    #print(smalt_out_37)
    
    count = 0

    for line in smalt_out_37:
        line = line.split('\t')
        print(line)

        match = int(len(line[9]) - int(line[12].split(':')[2]))

        if match <= 5:
            print(match)

            count +=1
    
    
    print(count)
                



    # smalt_out_38 = subprocess.run(cmd_38, shell = True, stdout = subprocess.PIPE).stdout.decode("ascii").strip()
    # smalt_out_38 = [line for line in smalt_out_38.split("\n") if not line.startswith("@")]

    for line in smalt_out_38:
        line = line.split('\t')

        match = 0

        if chrom == line[2]:
            # get just primers on correct chromosome
            match = int(len(line[9]) - int(line[12].split(':')[2]))
        
            if match <= 5:
                match_list2.append(match)





if __name__ == "__main__":
    primers = Models.PrimerDetails.objects.all()

    primers_file = "smalt_temp.fasta"

    main()