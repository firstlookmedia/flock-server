#!/bin/sh
docker run -it -w /app \
  -v $(pwd):/app \
  python:3.7.3-stretch \
  sh -c "pip install pipenv; bash"
