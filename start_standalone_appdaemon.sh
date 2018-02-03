#!/bin/bash

START_TIME='2016-06-06 03:59:50'
# Uncomment for debug mode:
DEBUG_MODE='-D DEBUG'

docker run \
  -it \
  --rm \
  --name=standalone-appdaemon \
  -p "5050:5050" \
  -v $(pwd)/conf:/conf \
  acockburn/appdaemon:latest \
  appdaemon -c /conf -s "$START_TIME" $DEBUG_MODE