FROM python:3.8

ENV PYTHONUNBUFFERED 1
# Sets the container's working directory to /app
WORKDIR /ga
# Copies all files from our local project into the container
COPY ./ ./
# runs the pip install command for all packages listed in the requirements.txt file
RUN ls
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
