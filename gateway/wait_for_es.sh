#!/bin/bash
until curl ${ELASTICSEARCH_HOSTS}
do
  echo Waiting for elasticsearch
  sleep 5
done
