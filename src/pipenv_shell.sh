#!/bin/sh
docker run -it -w /app \
  -v $(pwd):/app \
  python:3.8-buster \
  sh -c "pip install pipenv; bash"
