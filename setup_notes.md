## Notes for setting up / running Genetics Ark

requirements:
- install python packages from requirements.txt
- add email account credentials to config.py to send account authorisation
  emails from
- setup send grid account and store API key linked to above email account in
  config.py
- reccommended: create Django admin user (https://docs.djangoproject.com/en/3.1/intro/tutorial02/)


- requires config.py in ga_core, includes:
    - SECRET_KEY = Django secret key
    - AUTH_TOEKN = DNAnexus auth token for making dx queries
    - EMAIL_USER = email address of account to send emails from for new account
      authentication
    - EMAIL_PASSWORD = password for above email account
    - SEND_GRID_API_KEY = API key for sendgrid account linked to email
    - GOOGLE_ANALYTICS = token for Google analytics
    - PROD_HOST = host address for production
    - DEBUG_HOST = host address for debug/dev
    - PROD_DATABASE = db credentials for production (if used)
    - DEBUG_DATABASE = db credentials for debug/dev (if used)

- DNAnexus_IGV
    - requires cron job running every hour to run find_dx_bams.py to keep JSON
      up to date

- primer_designer
    - requires cron job running regularly to clear tmp directory of generated reports
