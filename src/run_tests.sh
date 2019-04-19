#!/bin/bash

BLUE='\033[0;34m'
NC='\033[0m' # No Color

printf "${BLUE}* Building gateway container${NC}\n"
docker build -t server .
echo

printf "${BLUE}* Starting containers${NC}\n"
docker network create testnet
docker run -d \
  --net testnet \
  --name test-elasticsearch \
  -e xpack.security.enabled=false \
  -e transport.host=localhost \
  elasticsearch:6.6.2@sha256:59dd45d05fe89cd713dfc20874c6298e1ec7eaf384e58410b677b9dead6986f1
docker run -d \
  --net testnet \
  --name test-server \
  -e ELASTICSEARCH_HOSTS=http://test-elasticsearch:9200 \
  server
echo

printf "${BLUE}* Waiting for elasticsearch${NC}\n"
docker exec -it test-server ./wait_for_es.sh
echo

printf "${BLUE}* Running tests${NC}\n"
docker exec -it test-server pipenv run python -m pytest
echo

printf "${BLUE}* Stopping containers${NC}\n"
docker stop test-elasticsearch
docker stop test-server
docker rm test-elasticsearch
docker rm test-server
docker network rm testnet
