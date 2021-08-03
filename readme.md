<div style="text-align: justify">

# Genetics Ark

Genetics Ark is a Django based web interface for hosting apps used by clinical scientists for managing and interpretating sequencing data.

## Requirements

- MySQL database for storing user accounts
- SMTP email credentials for sending user account activation links
- GRCh37/38 reference files for primer designer
- Docker (optional)
- Python packages (`requirements.txt`)


## Setup and Running 

Genetics Ark requires confidential variables be passed in a `.env` file, this sets the variables to the environment and allows them to be accessible to Django.
Once populated, this can be passed as the last argument when running from the cmd line (i.e. `python manage.py runserver <host>:<port> genetics_ark.env`) or with the `--env-file` argument if running with Docker.

### Running in development

For local development, not all the variables in the `.env` file are required to be filled if not being used (i.e. those for primer designer or email credentials), but the variable name must be present and left blank (see `example.env`).
A MySQL database is required, the models building to the database and credentials adding to the `.env` file.

### Running in production

Steps for deploying to production:

- local MySQL database created and mysqld running
- populated `.env` file
  - ensure `debug=False` is set
- models migrated to database:
  - with docker: 
    - `docker <image-name> sh -c "python manage.py makemigrations”`
    - `docker run <image-name> sh -c "python manage.py migrate”`
  - without docker:
    - `python manage.py makemigrations`
    - `python manage.py migrate`
- collect static files to serve
  - with docker: `docker run <image-name> sh -c "python manage.py collectstatic --noinput"`
  - without docker: `python manage.py collectstatic`
- start server:
  - with docker: 
    `docker run --env-file ark.env`
    `-v /home/\$USER/reference_files:/reference_files ` 
    `-v /var/log/genetics-ark/:/home/ga/logs `
    `-p80:8000 --network=host <image-name>`
  - without docker: `python manage.py runserver <host>:<port> ark.env`



<br></br>

## Current apps:

 - **Accounts**: Django user accounts, limits access to those with NHS email addresses through Django email authentication tokens. This also requires both
   an email and SendGrid account for sending emails from.

 - **Primer designer**: app for designing new sequencing primers, utilises primer3 for designing primers and returns a .pdf report.
  
 - **DNAnexus_to_igv**: app to link samples stored in the DNAnexus cloud platform with Genetics Ark. On searching for a sample, if it is found within a "002" sequencing project within DNAnexus, download urls are provided for the BAM and index file to load within IGV installed on a PC. A link to stream the BAM directly to IGV.js is also provided.<br>
n.b. find_dx_002_bams.py must first be run to generate a .json of samples in DNAnexus, this should be regularly run to stay up to date (i.e. via cron job). 

## Apps in development:

- **Primer database**: app to provide a web interface for interacting with the MySQL primer database, created to replace the current .xlsx "database". This will allow scientists to easily store new primer(s) and search for previously used ones, storing all relevant information to each primer. It also includes SNP checking functionality to automatically find variants present within the primer sequence against gnomAD.


</div>
