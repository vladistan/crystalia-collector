#!/bin/bash

set -e

VERSION=0.13

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
docker build -t crystalia:$VERSION .
# Tag and push to AWS ECR
ECR_REPO="${ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/crystalia-collector-batch-repo"
docker tag crystalia:$VERSION $ECR_REPO:v$VERSION
docker tag crystalia:$VERSION $ECR_REPO:latest
docker push $ECR_REPO:v$VERSION
docker push $ECR_REPO:latest

# Tag and push to Docker Hub
DOCKER_HUB_REPO="vladistan/crystalia-collector"
docker tag crystalia:$VERSION $DOCKER_HUB_REPO:v$VERSION
docker tag crystalia:$VERSION $DOCKER_HUB_REPO:latest
docker push $DOCKER_HUB_REPO:v$VERSION
docker push $DOCKER_HUB_REPO:latest
