import re

from django import forms

FUSION_PATTERN = (
    r"^[a-z0-9]+:[0-9]+:[ab]:[-]?1\s+[a-z0-9]+:[0-9]+:[ab]:[-]?1\s+grch3[78]$"
)


class RegionsForm(forms.Form):
    """Form for entering regions to design primers on"""

    regions = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "Enter Target Region(s)", "rows": 3}
        )
    )

    def clean_regions(self):
        """Function to validate input regions"""
        cleaned_data = self.cleaned_data

        for line in cleaned_data["regions"].split("\n"):
            if line.count(":") > 1:
                line = line.replace('\t', ' ').split(maxsplit=1)[
                    -1
                ]  # skip the first part (primer name)

                # fusion design given, expected to be in the format
                # chr:pos:side:strand chr:pos:side:strand build fusion
                line = line.rstrip("fusion").strip().lower()

                match = re.search(FUSION_PATTERN, line)

                if not match:
                    raise forms.ValidationError(
                        f"Fusion design {line} not in the correct format"
                    )
            else:
                # normal design checking
                line = line.rstrip("\r").replace(
                    "\t", " "
                )  # deal with tab-delimited inputs
                fields: list[str] = line.split(" ")

                # strip empty spaces in cases where multiple spaces used
                fields = [x for x in fields if x.strip()]

                if len(fields) != 3:
                    # each line should have 3 pieces of information:
                    # primer-name & chr:pos & build
                    raise forms.ValidationError(
                        (
                            f"{line} not in correct format. "
                            "Please see the examples for correct formatting"
                        )
                    )

                _, chromosome_position, build = fields

                if build.lower() not in ["grch37", "grch38"]:
                    # Check on valid reference names
                    raise forms.ValidationError(
                        "{} invalid reference\
                        name".format(
                            build
                        )
                    )

                # split chr and postion, will either be chr:pos or chr:pos-pos
                pos_fields = re.split("[:]", chromosome_position)
                match = re.search(r"^[0-9]+[-]?[0-9]*$", pos_fields[1])

                if not match:
                    raise forms.ValidationError(f"{line} chr/position in wrong format")

                chromosomes = [str(x) for x in range(1, 23)]
                chromosomes.extend(["X", "Y", "MT"])

                # Check on valid chromosome names
                if pos_fields[0].upper() not in chromosomes:
                    raise forms.ValidationError(
                        f"{pos_fields[0]} is not a valid chromosome name"
                    )
