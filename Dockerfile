# syntax=docker/dockerfile:1

FROM python:3.10.6-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app app
COPY settings.yaml settings.yaml

CMD [ "python3", "app/main.py"]