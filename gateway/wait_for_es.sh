#!/bin/bash
until curl --cacert /usr/share/ca-certificates/ca.crt -u "elastic:${ELASTIC_PASSWORD}" "${ELASTICSEARCH_HOSTS}"
do
  echo Waiting for elasticsearch
  sleep 5
done
