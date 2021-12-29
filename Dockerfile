FROM python:3.9.4-slim-buster
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD . /code/

RUN apt-get update && apt-get install -y wget && rm -rf /var/lib/apt/lists/* && pip install -r requirements.test.txt
