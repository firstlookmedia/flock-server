#!/bin/bash
until curl http://${ELASTICSEARCH_HOST}:9200
do
  echo Waiting for elasticsearch
  sleep 5
done
