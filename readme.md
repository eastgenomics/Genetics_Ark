<div style="text-align: justify">

# Genetics Ark

Genetics Ark is a Django based web interface for hosting apps used by clinical scientists for managing and interpretating sequencing data.

## Current apps:

 - **Accounts**: Django user accounts, limits access to those with NHS email addresses through Django email authentication tokens. This also requires both
   an email and SendGrid account for sending emails from.

 - **Primer designer**: app for designing new sequencing primers, utilises primer3 for designing primers and returns a .pdf report.
  
 - **DNAnexus_to_igv**: app to link samples stored in the DNAnexus cloud platform with Genetics Ark. On searching for a sample, if it is found within a "002" sequencing project within DNAnexus, download urls are provided for the BAM and index file to load within IGV installed on a PC. A link to stream the BAM directly to IGV.js is also provided.<br>
n.b. find_dx_002_bams.py must first be run to generate a .json of samples in DNAnexus, this should be regularly run to stay up to date (i.e. via cron job). 

## Apps in development:

- **Primer database**: app to provide a web interface for interacting with the MySQL primer database, created to replace the current .xlsx "database". This will allow scientists to easily store new primer(s) and search for previously used ones, storing all relevant information to each primer. It also includes SNP checking functionality to automatically find variants present within the primer sequence against gnomAD.


</div>
