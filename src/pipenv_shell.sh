#!/bin/sh
docker run -it -w /app \
  -v $(pwd):/app \
  python:3.7.4-buster \
  sh -c "pip install pipenv; bash"
