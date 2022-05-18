# FROM python:3.8.10

# ENV PYTHONUNBUFFERED 1
# # Sets the container's working directory to /app
# WORKDIR /home/ga

# ADD requirements.txt ./

# RUN pip install -r requirements.txt

# ADD ./ ./

# EXPOSE 8000

# CMD ["gunicorn", "--bind", ":80", "--workers", "3", "ga_core.wsgi:application"]

# syntax=docker/dockerfile:1

FROM python:3.8.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /home/ga
COPY requirements.txt /home/ga/
RUN pip install -r requirements.txt
EXPOSE 8000
COPY . /home/ga/

CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "ga_core.wsgi:application"]