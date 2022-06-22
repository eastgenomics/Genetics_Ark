FROM python:3.8.10

RUN apt-get update && apt-get -y install -qq --force-yes cron
WORKDIR /home/ga

ENV PYTHONUNBUFFERED 1

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN crontab /etc/cron.d/crontab

RUN touch /var/log/cron.log

COPY . .