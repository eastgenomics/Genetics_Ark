from dna_features_viewer import GraphicFeature, GraphicRecord
import matplotlib.pyplot as plt

import os
import sys

def get_data_from_django(primer1, primer2):
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

    return name1, start1_37, end1_37, strand1, name2, start2_37, end2_37, strand2


def main(
    seq_start, sequence,
    name1, start1, end1, strand1,
    name2, start2, end2, strand2
):
    if not os.path.exists('utils/primer_visualization/{}-{}.pdf'.format(name1, name2)):
        print("not exists")
        chunks = [sequence[i:i+80] for i in range(0, len(sequence), 80)]

        primers = [
            GraphicFeature(start=start1, end=end1, strand=strand1, color="#ffd700",
                            label=name1),
            GraphicFeature(start=start2, end=end2, strand=strand2, color="#cffccc",
                            label=name2)
        ]

        records = []

        for i, chunk in enumerate(chunks):
            records.append(
                GraphicRecord(sequence=chunk, first_index=min(start1, start2)+i*80, sequence_length=80, features=primers)
            )

        fig, axes = plt.subplots(nrows=len(chunks), figsize=(12, 14))

        for i, ax in enumerate(axes):
            ax.ticklabel_format(useOffset=False, style='plain')
            record = records[i]
            record.plot(ax=ax)
            record.plot_sequence(ax = ax, background = None)

        print(os.getcwd())
        fig.savefig('utils/primer_visualization/{}-{}.pdf'.format(name1, name2), format="pdf")
        return True
    else:
        return False



if __name__ == "__main__":
    sequence = "TCAAGCTTGCCATCTCTTCATGTTAGGAAACAAAAAGCCCTAGAAGCAGAATTAGATGCTCAGCACTTATCAGAAACTTTTGACAATATAGACAATTTAAGTCCCAAGGCATCTCATCGTAGTAAGCAGAGACACAAGCAAAGTCTCTATGGTGATTATGTTTTTGACACCAATCGACATGATGATAATAGGTCAGACAATTTTAATACTGGCAACATGACTGTCCTTTCACCATATTTGAATACTACAGTGTTACCCAGCTCCTCTTCATCAAGAGGAAGCTTAGATAGTTCTCGTTCTGAAAAAGATAGAAGTTTGGAGAGAGAACGCGGAATTGGTCTAGGCAACTACCATCCAGCAACAGAAAATCCAGGAACTTCTTCAAAGCGAGGTTTGCAGATCTCCACCACTGCAGCCCAGATTGCCAAAGTCATGGAAGAAGTGTCAGCCATTCATACCTCTCAGGAAGACAGAAGTTCTGGGTCTACCACTGAATTACATTGTGTGACAGATGAGAGAAATGCACTTAGAAGAAGCTCTGCTGCCCATACACATTCAAACACTTACAATTTCACTAAGTCGGAAAATTCAAATAGGACATGTTCTATGCCTTATGCCAAATTAGAATACAAGAGATCTTCAAATGATAGTTTAAATAGTGT"
    seq_start = 112173530
    name1 = "Primer_1"
    start1 = 112173630
    end1 = 112173650
    strand1 = +1
    name2 = "Primer_2"
    start2 = 112174069
    end2 = 112174091
    strand2 = -1

    main(seq_start, sequence, name1, start1, end1, strand1, name2, start2, end2, strand2)