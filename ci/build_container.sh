#!/bin/bash

set -e

VERSION=0.12

docker build -t crystalia:$VERSION .
docker tag crystalia:$VERSION 543533956684.dkr.ecr.us-east-1.amazonaws.com/crystalia-collector-batch-repo:v$VERSION
docker push 543533956684.dkr.ecr.us-east-1.amazonaws.com/crystalia-collector-batch-repo:v$VERSION

