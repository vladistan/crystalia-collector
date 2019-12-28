FROM python:3.8.1-alpine3.11

RUN mkdir -p /pkg
ADD . /pkg
WORKDIR /pkg
RUN pip install -e .
