FROM python:3.8.10

ENV PYTHONUNBUFFERED 1
WORKDIR /home/ga

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY ./ ./

EXPOSE 8000

CMD ["gunicorn", "--bind", ":80", "--workers", "3", "ga_core.wsgi:application"]