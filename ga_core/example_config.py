# django secret key
SECRET_KEY = ""

# DNAnexus auth token
AUTH_TOKEN = ""

# email account and sendgrid key for account emails
EMAIL_USER = ""
EMAIL_PASSWORD = ""
SEND_GRID_API_KEY = ""

GOOGLE_ANALYTICS = ""

# django database settings
PROD_HOST = ""
DEBUG_HOST = [""]
PROD_DATABASE = ""
DEBUG_DATABASE = ""

# path to primer3 python script, used for primer designer
primer_designer_path = ""

# IGV ref file paths
fasta_37 = ""
fasta_idx_37 = ""
cytoband_37 = ""
refseq_37 = ""

fasta_38 = "https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/hg38/hg38.fa"
fasta_idx_38 = "https://s3.amazonaws.com/igv.broadinstitute.org/genomes/seq/hg38/hg38.fa.fai"
cytoband_38 = "https://s3.amazonaws.com/igv.broadinstitute.org/annotations/hg38/cytoBandIdeo.txt"
refseq_38 = "https://s3.amazonaws.com/igv.org.genomes/hg38/refGene.txt.gz"