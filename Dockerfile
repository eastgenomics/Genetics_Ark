FROM primer_designer:latest

ENV PYTHONUNBUFFERED 1
# Sets the container's working directory to /app
WORKDIR /home/ga

# Copies all files from our local project into the container
# COPY ./ ./


# EXPOSE 8000

# CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]


ADD requirements.txt ./
RUN pip install -r requirements.txt

# RUN set -ex \
#     pip install --upgrade pip \
#     pip install --no-cache-dir -r requirements.txt 

ADD ./ ./

# WORKDIR /app

# ENV VIRTUAL_ENV /env
# ENV PATH /env/bin:$PATH

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "ga_core.wsgi:application"]