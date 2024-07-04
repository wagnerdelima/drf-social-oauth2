FROM python:3.13.0b2-slim
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code

ADD . /code/

RUN pip install --no-cache-dir --upgrade pip && apt-get update && apt-get install -y --no-install-recommends wget && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir -r requirements.test.txt
