#!/bin/sh
docker run -it -v $(pwd):/app -w /app -p 5000:5000 \
  python:3.7.2-stretch@sha256:8bfb2d646119faeb1892ddf9668eeb08a8938626f64b91100a31a8dea46ec67d \
  sh -c "pip install pipenv; pipenv install; bash"
