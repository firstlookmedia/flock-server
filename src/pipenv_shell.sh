#!/bin/sh
docker run -it -w /app \
  -v $(pwd):/app \
  python:3.7.2-stretch@sha256:8bfb2d646119faeb1892ddf9668eeb08a8938626f64b91100a31a8dea46ec67d \
  sh -c "pip install pipenv; bash"
