FROM primer_designer:2.0.2

WORKDIR /home/ga

ENV PYTHONUNBUFFERED 1

COPY requirements.txt ./

RUN pip install -r requirements.txt

COPY . .