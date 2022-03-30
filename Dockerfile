FROM python:3.11.0a6-slim-buster
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD . /code/

RUN apt-get update && apt-get install -y --no-install-recommends wget && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir -r requirements.test.txt
