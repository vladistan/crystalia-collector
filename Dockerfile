FROM python:3.12

RUN mkdir -p /pkg
COPY . /pkg
WORKDIR /pkg
RUN pip install --no-cache-dir -e . && \
    pip install --no-cache-dir awscli==2.17.37
