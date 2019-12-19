#!/usr/bin/env python

import argparse
import requests

def fetch(jsondata, url="https://gnomad.broadinstitute.org/api"):
    # The server gives a generic error message if the content type isn't
    # explicitly set
    headers = {"Content-Type": "application/json", "charset": "utf-8"}
    response = requests.post(url, json=jsondata, headers=headers)
    json = response.json()

    if "errors" in json:
        return 

    return json

def snp_check_query(gene_symbol, ref):
    if ref == "37":
        dataset = "gnomad_r2_1"
        query = """
        {{
            gene(gene_symbol: "{}") {{
                variants(dataset: {}) {{
                    pos
                    variant_id: variantId
                    exome {{
                        populations {{
                            ac
                            an
                        }}
                    }}
                    genome {{
                        populations {{
                            ac
                            an
                        }}
                    }}
                }}
            }}
        }}
        """.format(gene_symbol, dataset)

    elif ref == "38":
        dataset = "gnomad_r3"
        query = """
        {{
            gene(gene_symbol: "{}", reference_genome: GRCh38) {{
                variants(dataset: {}) {{
                    pos
                    variant_id: variantId
                    exome {{
                        populations {{
                            ac
                            an
                        }}
                    }}                
                    genome {{
                        populations {{
                            ac
                            an
                        }}
                    }}                        
                }}
            }}
        }}
        """.format(gene_symbol, dataset)


    # This part will be JSON encoded, but with the GraphQL part left as a
    # glob of text.
    req_variantlist = {
        "query": query,
        "variables": {}
    }

    response = fetch(req_variantlist)

    if response:
        return response["data"]["gene"]["variants"]
    else:
        return


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()

#     parser.add_subparsers()