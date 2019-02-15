#!/bin/bash
until curl http://elasticsearch:9200
do
  echo Waiting for elasticsearch
  sleep 5
done
