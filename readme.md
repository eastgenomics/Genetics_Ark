<div style="text-align: justify">

# Genetics Ark

Genetics Ark is a Django based web interface for hosting apps used by clinical scientists for managing and interpretating sequencing data.

## Requirements

- GRCh37/38 reference files for Primer Designer (human reference genome & SNPs VCF)
- reference files for IGV.js (fasta, fai, cytoband, refseq)
- Docker & Docker Compose
- Primer Designer (deployed on Docker)

#### primer designer
Genetic Ark allows primer input submission: `<chromosome>:<position> <genome build>`

  
## Setup and Running 

Genetics Ark requires confidential environment variables in a `config.txt` or `.env` file. 
  
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


### Running in Production
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

## Current Apps

 - **Primer designer**: App for designing new sequencing primers, utilises primer3 for designing primers and returns a .pdf report
  
 - **DNAnexus_to_igv**: App to link samples stored in the DNAnexus cloud platform with Genetics Ark. On searching for a sample (BAM or CNV), if it is found within a 002 sequencing project within DNAnexus (for BAM) or in `PROJECT_CNVS` (for CNVs), download urls are provided for the file and its index file to load within IGV installed on a PC. A link to stream the file directly to IGV.js is also provided. cron container will periodically run find_dx_data.py to update the `.json` of samples
  
## Apps in Development:
