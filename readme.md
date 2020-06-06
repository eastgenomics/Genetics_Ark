<div style="text-align: justify">

# Genetics Ark

Genetics Ark is a Django based web interface for hosting apps used by clinical scientists for managing and interpretating sequencing data. Currently, the core functionality resides in the Genetics Ark app, which connects to the Gemini MySQL variant database. This allows for scientists to search for a sample number, and then perform a reanalysis with either a set of gene(s) and / or panel(s), generating a new .xlsx report. From here,they may also view the sample in the web based IGV.js.

## Current apps:

 - **Primer designer**: app for designing new sequencing primers, utilises primer3 for designing primers and returns a .pdf report.
  
 - **DNAnexus_to_igv**: app to link samples stored in the DNAnexus cloud platform with Genetics Ark. On searching for a sample, if it is found within a "002" sequencing project within DNAnexus, download urls are provided for the BAM and index file to load within IGV installed on a PC. A link to stream the BAM directly to IGV.js is also provided.

## Apps in development:

- **Primer database**: app to provide a web interface for interacting with the MySQL primer database, created to replace the current .xlsx "database". This will allow scientists to easily store new primer(s) and search for previously used ones, storing all relevant information to each primer. It also includes SNP checking functionality to automatically find variants present within the primer sequence against gnomAD.
  
- **HGMD / ClinVar annotation**: app to add HGMD and ClinVar annotation to existing variants within the Gemini database.

- **CNV**: app to run the DECoN CNV caller to identify CNVs for each sample, and provide a view for visualising identified CNVs.

### Notes:

- the core Django (i.e. settings.py) is within django_example directory
- lots of legacy files and code that can be removed

</div>