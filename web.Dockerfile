FROM python:3.8

RUN apt-get update -y
RUN apt-get install -y build-essential gcc python3-dev libldap2-dev libsasl2-dev ldap-utils tox lcov valgrind vim nano jq procps

WORKDIR /home/ga

ENV PYTHONUNBUFFERED 1

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .