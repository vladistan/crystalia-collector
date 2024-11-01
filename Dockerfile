FROM python:3.12

RUN mkdir -p /pkg
ADD . /pkg
WORKDIR /pkg
RUN pip install -e .
RUN pip install awscli
