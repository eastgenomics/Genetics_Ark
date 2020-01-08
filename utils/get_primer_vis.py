from dna_features_viewer import GraphicFeature, GraphicRecord
import matplotlib.pyplot as plt

from collections import defaultdict
import math
import os
import sys


def get_data_from_django(primer1, primer2):
    """ Parse data from primer model object """

    primers = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    name1 = primer1.name
    name2 = primer2.name
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


def main(seq_starts, samtools_output, primer_data):
    """ Given sequence and primer data, plot the primers on the sequence """

    name1, name2 = list(primer_data.keys())
    res = {}

    if not os.path.exists("primer_db/primer_visualization") or not os.path.isdir("primer_db/primer_visualization"):
        os.mkdir("primer_db/primer_visualization")

    for ref, sequence in samtools_output.items():
        if not os.path.exists("primer_db/primer_visualization/{}-{}_{}.pdf".format(name1, name2, ref)):
            records = []
            primers = []
            snps = []
            seq_start = seq_starts[ref]

            for name, refs in primer_data.items():
                coordinates = refs[ref]["coordinates"]
                strand = refs[ref]["strand"]
                
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

            seq_record = GraphicRecord(
                sequence = sequence, 
                first_index=seq_start, 
                sequence_length = len(sequence), 
                features = primers+snps,
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

    main(seq_start, sequence, data)