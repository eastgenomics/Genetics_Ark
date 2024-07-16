<div style="text-align: justify">

# Genetics Ark

Genetics Ark is a Django based web interface for hosting apps used by clinical scientists for managing and interpretating sequencing data.

## Requirements

- GRCh37/38 reference files for primer designer (human reference genome & SNPs VCF)
- reference files for IGV.js (fasta, fai, cytoband, refseq)
- Docker & Docker Compose
- [Primer Designer](https://github.com/eastgenomics/primer_designer) (deployed on Docker)

#### primer designer
Genetics Ark allows primer input submission: `<chromosome>:<position> <genome build>`

### igv
Genetics Ark allows igv searching for BAM or CNV samples (login required)

  
## Setup and Running 

Genetics Ark requires 2 local files containing environment variables:
- A small `.env` file, kept in the same directory as your docker-compose.yml file. This only contains paths to mounted volumes, plus the path to the main config.txt file, given by GA_CONFIG_PATH. By adjusting this, the user can change their main config path for the docker-compose.yml without having to edit the docker-compose.yml directly. See the example.env.
- A 'config.txt' file, which contains the majority of the environment variables. See example.config.txt for annotations.

In addition, you'll need to check that nginx/nginx.conf displays the correct ports for Genetics Ark. In the upstream ga{} section, ensure the port matches the one for genetics-ark-web.


### docker-compose

#### cron
- By default, find_dx_data.py runs every 15 minutes, and checks for new samples in DNAnexus which can be made available to IGV. A script which clears out a temporary directory runs every morning at 2am.
- Both the above cron jobs, on successful completion, emit text log files plus Prometheus-formatted metric files. The metrics can be used with Prometheus to send alerts, if they do not run when expected.
- Edit the `crontab` file to tweak the cron schedule.
```
# start cron
0 2 * * * rm -rf /home/tmp/* && echo "`date +\%Y\%m\%d-\%H:\%M:\%S` tmp folder cleared" >> /home/log/ga-cron.log 2>&1 && echo "`date +\%Y\%m\%d-\%H:\%M:\%S` sample file updated" >> /home/log/ga-cron.log 2>&1 && /usr/local/bin/python -u /home/emit_prom_metric.py "ga_temp_deleted"
*/15 * * * * /usr/local/bin/python -u /home/find_dx_data.py >> /home/log/ga-cron.log 2>&1 && echo "`date +\%Y\%m\%d-\%H:\%M:\%S` sample file updated" >> /home/log/ga-cron.log 2>&1 && /usr/local/bin/python -u /home/emit_prom_metric.py "ga_cron_completed"
# end cron
```
All cron run logs will be stored in cron container `/home/log/cron.log`

### Running in local system
Ensure the following environment variables are correct:

- change logging location in `ga_core/settings.py`
- change database setting to localhost database
- change redis setting to localhost redis

You must also run a server, with `python manage.py runserver`

### Running in production
Ensure `GENETIC_DEBUG` is not in config file, to run in production mode
```
docker compose build
docker compose up db -d # start db first and create a database named genetics
docker compose up web -d # start web container and run python manage.py migrate
docker compose up
```
This will spin up 6 containers: `web`, `cron`, `nginx`, `database`, `redis`, `djangoq`

#### ga_web
Main django web interface

#### ga_cron
Cron schedule for updating igv samples jsons & removing generated primer design PDFs in `/home/tmp`

#### ga_nginx
Nginx server used to serve django staticfiles, reference files for `igv.js` and to download primer designer generated zipfile

#### ga_djangoq
Django-q queue system for primer design task

#### ga_redis
Redis as queue broker

#### genetics_db
MySQL database

## Environments
View the 'example.env' file for descriptions of the required environment variables, which should be stored in a '.env' file locally. .env files must not be version-controlled.

## Current Apps

 - **Primer designer**: App for designing new sequencing primers, utilises primer3 for designing primers and returns a .pdf report
  
 - **DNAnexus_to_igv**: App to link samples stored in the DNAnexus cloud platform with Genetics Ark. On searching for a sample (BAM or CNV), if it is found within a 002 sequencing project within DNAnexus (for BAM) or in `PROJECT_CNVS` (for CNVs), download urls are provided for the file and its index file to load within IGV installed on a PC. A link to stream the file directly to IGV.js is also provided. cron container will periodically run find_dx_data.py to update the `.json` of samples
  
## Apps in Development:

N/A