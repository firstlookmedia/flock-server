#!/bin/bash

BLUE='\033[0;34m'
NC='\033[0m' # No Color

printf "${BLUE}* Building containers${NC}\n"
docker build -t gateway gateway
echo

printf "${BLUE}* Starting containers${NC}\n"
docker network create testnet
docker run -d --net testnet --name test-elasticsearch -e xpack.security.enabled=false -e transport.host=localhost elasticsearch:6.6.0@sha256:ed1f27b9a16dc29d19fc607a1e6e281d1ddf83d81734427d895f5b91c23a6ee5
docker run -d --net testnet --name test-gateway -e ELASTICSEARCH_HOSTS=http://test-elasticsearch:9200 gateway
echo

printf "${BLUE}* Waiting for elasticsearch${NC}\n"
docker exec -it test-gateway ./wait_for_es.sh
echo

printf "${BLUE}* Running tests${NC}\n"
docker exec -it test-gateway pipenv run python -m pytest
echo

printf "${BLUE}* Stopping containers${NC}\n"
docker stop test-elasticsearch
docker stop test-gateway
docker rm test-elasticsearch
docker rm test-gateway
docker network rm testnet
