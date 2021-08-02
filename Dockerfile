FROM primer_designer:1.2

ENV PYTHONUNBUFFERED 1
# Sets the container's working directory to /app
WORKDIR /home/ga

ADD requirements.txt ./

RUN pip install -r requirements.txt

ADD ./ ./

EXPOSE 8000

CMD ["gunicorn", "--bind", ":80", "--workers", "3", "ga_core.wsgi:application"]