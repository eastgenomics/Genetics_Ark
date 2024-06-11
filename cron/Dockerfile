FROM python:3.8-slim

RUN apt-get update && apt-get -y install -qq --force-yes cron
RUN apt-get -y install vim nano jq
RUN apt-get install gcc python3-dev -y

WORKDIR /home

ENV PYTHONUNBUFFERED 1

COPY requirements.txt find_dx_data.py ./

RUN pip install -r requirements.txt

# comment out a line in pam.d which stops crons running otherwise
RUN sed -e '/session required pam_loginuid.so/ s/^#*/#/' -i /etc/pam.d/cron

COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN crontab /etc/cron.d/crontab