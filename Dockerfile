FROM python:3.9.2
# FROM python:3.9.4-slim-buster
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD . /code/

RUN pip install -r requirements.test.txt
