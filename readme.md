<div style="text-align: justify">

# Genetics Ark

Genetics Ark is a Django based web interface for hosting apps used by clinical scientists for managing and interpretating sequencing data.

## Requirements

- GRCh37/38 reference files for primer designer (human reference genome & SNPs VCF)
- reference files for IGV.js (fasta, fai, cytoband, refseq)
- Docker & Docker Compose
- [Primer Designer](https://github.com/eastgenomics/primer_designer) (deployed on Docker)

#### primer designer
Genetic Ark allows primer input submission: `<chromosome>:<position> <genome build>`

  
## Setup and Running 

Genetics Ark requires environment variables in a `config.txt` or `.env` file (see example.env)
  
Edit `env_file` in `docker-compose.yml` to point to your `.env` file

### docker-compose

#### cron
- Edit `crontab` file to tweak cron schedule
```
# start cron
0 2 * * * rm -rf /home/tmp/* && echo "`date +\%Y\%m\%d-\%H:\%M:\%S` tmp folder cleared" >> /home/log/ga-cron.log 2>&1
0 2 * * * /usr/local/bin/python -u /home/find_dx_data.py >> /home/log/ga-cron.log 2>&1
# end cron
```
Check schduled cron is running by accessing cron container `docker exec -it <container id> bash` then `tail /home/log/cron.log`. 

All cron run log will be stored in cron container `/home/log/cron.log`

### Running in local system
- change logging location in `ga_core/settings.py`
- collect static files `python manage.py collectstatic`
- run server `python manage.py runserver`

### Running in production
Ensure `GENETIC_DEBUG` is not in config file to run in production mode
```
docker compose build
docker compose up
# Server should be running in http://localhost:1337 if in local development
```
This will spin up 3 containers: `genetics_ark_web`, `genetics_ark_cron`, `genetics_ark_nginx`

#### genetics_ark_web
Main web interface

#### genetics_ark_cron
Cron schedule for updating BAM samples jsons & removing generated primer design PDFs in `/home/tmp`

#### genetics_ark_nginx
Nginx server used to serve django staticfiles, reference files for `igv.js` and to download primer designer generated zipfile

*access individual container using cmd: `docker exec -it <container id> bash`

## Environments
```
PRIMER_VERSION - primer designer version to be displayed in output PDF

REF_37 - directory pathway (docker) to grch37 reference
SNP_37 - directory pathway (docker) to snp37 gnomad file

REF_38 - directory pathway (docker) to grch38 reference
SNP_38 - directory pathway (docker) to snp38 gnomad file

PRIMER37_TEXT - text displayed in output primer PDF for grch37 snp file
PRIMER38_TEXT - text displayed in output primer PDF for grch38 snp file

SECRET_KEY - django secret key
GENETIC_DEBUG - whether to run in debug or not
CSRF_TRUSTED_ORIGINS - hostname for csrf form submission
PRIMER_DOWNLOAD - primer PDF download link (e.g. http://localhost:80/genetics_ark)

DNANEXUS_TOKEN - DNANexus auth token

BIND_DN - ldap bind username
BIND_PASSWORD - ldap bind password
AUTH_LDAP_SERVER_URI - ldap uri
LDAP_CONF - ldap base_dn

PROD_HOST - production host (django)
DEBUG_HOST - debug host (django) e.g. *

DB_NAME - db name
DB_USERNAME - db username
DB_PASSWORD - db password
DB_PORT - db port
MYSQL_ROOT_PASSWORD - mysql root password


GENOMES - url to genomes.json used by igv

FASTA_37 - url to fasta37 used by igv
FASTA_IDX_37 -url to fasta37_index used by igv
CYTOBAND_37 - url to cytoband37 used by igv
REFSEQ_37 - url to refseq37 used by igv
REFSEQ_INDEX_37 - url to refseq37_index used by igv

FASTA_38 - url to fasta38 used by igv
FASTA_IDX_38 - url to fasta38_index used by igv
CYTOBAND_38 - url to cytoband38 used by igv
REFSEQ_38 - url to refseq38 used by igv
REFSEQ_INDEX_38 - url to refseq38_index used by igv

DEV_PROJECT_NAME - name of dev project 003
PROJECT_CNVS - project-id of cnvs projects

SLACK_TOKEN - slack auth token

GRID_SERVICE_DESK - url for bioinformatics service desk
GRID_IVA - url for bioinformatics IVA
```

## Current Apps

 - **Primer designer**: App for designing new sequencing primers, utilises primer3 for designing primers and returns a .pdf report
  
 - **DNAnexus_to_igv**: App to link samples stored in the DNAnexus cloud platform with Genetics Ark. On searching for a sample (BAM or CNV), if it is found within a 002 sequencing project within DNAnexus (for BAM) or in `PROJECT_CNVS` (for CNVs), download urls are provided for the file and its index file to load within IGV installed on a PC. A link to stream the file directly to IGV.js is also provided. cron container will periodically run find_dx_data.py to update the `.json` of samples
  
## Apps in Development:
