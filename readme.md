<div style="text-align: justify">

# Genetics Ark

Genetics Ark is a Django based web interface for hosting apps used by clinical scientists for managing and interpretating sequencing data.

## Requirements

- GRCh37/38 reference files for Primer Designer (human reference genome & SNPs VCF)
- reference files for IGV.js (fasta, fai, cytoband, refseq)
- Docker & Docker Compose
- Primer Designer (deployed on Docker)

#### primer designer
When a primer input is submitted `<chromosome>:<position> <genome build>`, Genetic Ark calls the deployed primer designer in Docker 
  
```
docker run -v <reference-file-dir>:/reference_files -v <host-output-dir>:/home/primer_designer/output --env REF_37 --env DBSNP_37 <primer_image> python3 bin/primer_designer_region.py <cmd>
```
This will generate the primer PDFs at `<host-output_dir>` (host filesystem) which is also mounted to Genetic Ark (see `docker-compose.yml` `<output-dir>:/home/ga/tmp`), thus allow Genetic Ark to generate download link to download the `.zip` file to the end user


  
## Setup and Running 

Genetics Ark requires confidential environment variables in a `config.txt` or `.env` file. 
  
Edit `env_file` in `docker-compose.yml` to point to your `.env` file

### docker-compose

#### cron
- Edit `crontab` file to tweak cron schedule
```
# start cron
*/10 * * * * rm -rf /home/ga/tmp/* && echo "`date +\%Y\%m\%d-\%H:\%M:\%S` tmp folder cleared" >> /var/log/cron.log 2>&1
*/10 * * * * /usr/local/bin/python -u /home/ga/DNAnexus_to_igv/find_dx_data.py >> /var/log/cron.log 2>&1
# end cron
```
Check schduled cron is running by accessing cron container `docker exec -it <container id> bash` then `tail /var/log/cron.log`. 

All cron run log will be stored in cron container `/var/log/cron.log`


### Running in Production
```
docker compose build
docker compose up -d
# http://localhost:1337
```
This will spin up 3 containers: `genetics_ark_web`, `genetics_ark_cron`, `genetics_ark_nginx`

#### genetics_ark_web
Main web interface

#### genetics_ark_cron
Cron schedule for updating BAM jsons & removing generated primer design PDFs in `/home/ga/tmp`

#### genetics_ark_nginx
Nginx server used to serve django staticfiles, reference files for `igv.js` and to download primer designer zip file

*access individual container using cmd: `docker exec -it <container id> bash`

## Current Apps

 - **Primer designer**: App for designing new sequencing primers, utilises primer3 for designing primers and returns a .pdf report
  
 - **DNAnexus_to_igv**: App to link samples stored in the DNAnexus cloud platform with Genetics Ark. On searching for a sample (BAM or CNV), if it is found within a 002 sequencing project within DNAnexus (for BAM) or in `PROJECT_CNVS` (for CNVs), download urls are provided for the file and its index file to load within IGV installed on a PC. A link to stream the file directly to IGV.js is also provided. cron container will periodically run find_dx_data.py to update the `.json` of samples
  
## Apps in Development:
