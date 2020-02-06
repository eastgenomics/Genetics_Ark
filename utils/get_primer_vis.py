from dna_features_viewer import GraphicFeature, GraphicRecord
import matplotlib.pyplot as plt

from collections import defaultdict
import math
import os
import sys

GENES2TRANSCRIPTS = "/mnt/storage/data/NGS/nirvana_genes2transcripts"


def get_data_from_django(primer1, primer2):
    """ Parse data from primer model object """

    primers = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    name1 = primer1.name
    name2 = primer2.name
    gene = primer1.gene
    chrom = primer1.coordinates.chrom_no
    start1_37 = primer1.coordinates.start_coordinate_37
    end1_37 = primer1.coordinates.end_coordinate_37
    start2_37 = primer2.coordinates.start_coordinate_37
    end2_37 = primer2.coordinates.end_coordinate_37
    start1_38 = primer1.coordinates.start_coordinate_38
    end1_38 = primer1.coordinates.end_coordinate_38
    start2_38 = primer2.coordinates.start_coordinate_38
    end2_38 = primer2.coordinates.end_coordinate_38
    strand1 = primer1.coordinates.strand
    strand2 = primer2.coordinates.strand
    snp_info1 = primer1.snp_info
    snp_info2 = primer2.snp_info

    primers[name1]["37"]["chrom"] = chrom
    primers[name2]["37"]["chrom"] = chrom
    primers[name1]["38"]["chrom"] = chrom
    primers[name2]["38"]["chrom"] = chrom

    primers[name1]["37"]["gene"] = gene
    primers[name2]["37"]["gene"] = gene
    primers[name1]["38"]["gene"] = gene
    primers[name2]["38"]["gene"] = gene

    primers[name1]["37"]["coordinates"] = [start1_37, end1_37]
    primers[name1]["37"]["strand"] = strand1
    primers[name2]["37"]["coordinates"] = [start2_37, end2_37]
    primers[name2]["37"]["strand"] = strand2

    primers[name1]["38"]["coordinates"] = [start1_38, end1_38]
    primers[name1]["38"]["strand"] = strand1
    primers[name2]["38"]["coordinates"] = [start2_38, end2_38]
    primers[name2]["38"]["strand"] = strand2

    if snp_info1:
        for snp in snp_info1.split(";"):
            pos = snp.split(",")[1].split("-")[1]

            if "r2_1" in snp:
                primers[name1]["37"]["snps"].append(pos)
            elif "r3" in snp:
                primers[name1]["38"]["snps"].append(pos)

    if snp_info2:
        for snp in snp_info2.split(";"):
            pos = snp.split(",")[1].split("-")[1]

            if "r2_1" in snp:
                primers[name2]["37"]["snps"].append(pos)
            elif "r3" in snp:
                primers[name2]["38"]["snps"].append(pos)

    return primers


def get_transcript_from_nirvana(primer_gene, g2t_file = GENES2TRANSCRIPTS):
    """ Get the transcript from nirvana for given gene
    Needed for selecting exons in primer visualization
    """
    
    with open(g2t_file) as f:
        for line in f:
            gene, transcript = line.strip().split()
            gene = gene.upper()

            if gene == primer_gene:
                return transcript
    
    return


def get_all_exons(ref, primer_chrom, primer1_coordinates, primer2_coordinates, nirvana_transcript):
    """ Get all exons using nirvana gffs

    Args:
     - ref: str
     - primer_chrom: str
     - primer1_coordinates: tuple
     - primer2_coordiantes: tuple
     - nirvana_transcript: str

    Returns:
     - exons: list of tuple
    """

    exons = []
    left_most_coordinate = min(primer1_coordinates + primer2_coordinates)
    right_most_coordinate = max(primer1_coordinates + primer2_coordinates)


    with open("../data/{}_chr{}_all_exons.gff".format(ref, primer_chrom)) as f:
        for line in f:
            line = line.strip().split("\t")
            start = int(line[3])
            end = int(line[4])
            strand = line[6]
            annotations = line[8]

            if left_most_coordinate - 80 < end and right_most_coordinate + 80 > start:
                for data in annotations.split(";"):
                    if "gene_name" in data:
                        gene = data.split()[1].strip("\"")
                    
                    if "transcript_id" in data:
                        transcript = data.split()[1].strip("\"")
                        
                    if "exon_number" in data:
                        exon_nb = data.split()[1]

                if nirvana_transcript == transcript:
                    exons.append((start, end, strand, "{}_{}_exon{}".format(gene, transcript, exon_nb)))

    return exons


def main(seq_starts, samtools_output, primer_data):
    """ Given sequence and primer data, plot the primers on the sequence """

    name1, name2 = list(primer_data.keys())
    res = {}

    if not os.path.exists("primer_db/primer_visualization") or not os.path.isdir("primer_db/primer_visualization"):
        os.mkdir("primer_db/primer_visualization")

    for ref, sequence in samtools_output.items():
        if not os.path.exists("primer_db/primer_visualization/{}-{}_{}.pdf".format(name1, name2, ref)):
            coordinates_primers = []
            records = []
            primers = []
            snps = []
            exons_features = []
            seq_start = seq_starts[ref]

            for name, refs in primer_data.items():
                coordinates = refs[ref]["coordinates"]
                strand = refs[ref]["strand"]
                chrom = refs[ref]["chrom"]
                gene = refs[ref]["gene"]
                
                if refs[ref]["snps"]:
                    for pos in refs[ref]["snps"]:
                        pos = int(pos)
                        snps.append(
                            GraphicFeature(start=pos, end=pos+1, color="#ff0000", label="SNP")
                        )

                primers.append(
                    GraphicFeature(start=min(coordinates), end=max(coordinates) + 1, strand=int("{}1".format(strand)),
                                color="#ffd700", label=name)
                )

                coordinates_primers.append(coordinates)

            nirvana_transcript = get_transcript_from_nirvana(gene)

            if nirvana_transcript:
                exons = get_all_exons(ref, chrom, coordinates_primers[0], coordinates_primers[1], nirvana_transcript)

                for exon in exons:
                    start, end, strand, label = exon
                    exons_features.append(
                        GraphicFeature(start=start, end=end, strand=int("{}1".format(strand)),
                                    color="#002EFF", label=label)
                    )

            coor = coordinates_primers[0] + coordinates_primers[1]

            seq_record = GraphicRecord(
                sequence = sequence, 
                first_index=seq_start, 
                sequence_length = len(sequence), 
                features = primers+snps+exons_features,
                ticks_resolution=10
            )

            seq_record.plot_on_multiple_pages(
                "primer_db/primer_visualization/{}-{}_{}.pdf".format(name1, name2, ref),
                nucl_per_line = 80,
                lines_per_page = 10,
                plot_sequence = True
            )

            res[ref] = "created"
        else:
            res[ref] = "exists"

    return res



if __name__ == "__main__":
    sequence = {}
    seq_start = {}
    sequence["37"] = "TCAAGCTTGCCATCTCTTCATGTTAGGAAACAAAAAGCCCTAGAAGCAGAATTAGATGCTCAGCACTTATCAGAAACTTTTGACAATATAGACAATTTAAGTCCCAAGGCATCTCATCGTAGTAAGCAGAGACACAAGCAAAGTCTCTATGGTGATTATGTTTTTGACACCAATCGACATGATGATAATAGGTCAGACAATTTTAATACTGGCAACATGACTGTCCTTTCACCATATTTGAATACTACAGTGTTACCCAGCTCCTCTTCATCAAGAGGAAGCTTAGATAGTTCTCGTTCTGAAAAAGATAGAAGTTTGGAGAGAGAACGCGGAATTGGTCTAGGCAACTACCATCCAGCAACAGAAAATCCAGGAACTTCTTCAAAGCGAGGTTTGCAGATCTCCACCACTGCAGCCCAGATTGCCAAAGTCATGGAAGAAGTGTCAGCCATTCATACCTCTCAGGAAGACAGAAGTTCTGGGTCTACCACTGAATTACATTGTGTGACAGATGAGAGAAATGCACTTAGAAGAAGCTCTGCTGCCCATACACATTCAAACACTTACAATTTCACTAAGTCGGAAAATTCAAATAGGACATGTTCTATGCCTTATGCCAAATTAGAATACAAGAGATCTTCAAATGATAGTTTAAATAGTGT"
    seq_start["37"] = 112173530

    data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    name1 = "Primer_1"
    start1 = 112173630
    end1 = 112173650
    strand1 = "+"
    name2 = "Primer_2"
    start2 = 112174069
    end2 = 112174091
    strand2 = "-"

    data[name1]["37"]["coordinates"] = [start1, end1]
    data[name1]["37"]["strand"] = strand1
    data[name2]["37"]["coordinates"] = [start2, end2]
    data[name2]["37"]["strand"] = strand2

    start1 = [25025617, 25025633]
    end2 = [25025132, 25025151]

    get_all_exons("37", "X", start1, end2)

    # main(seq_start, sequence, data)