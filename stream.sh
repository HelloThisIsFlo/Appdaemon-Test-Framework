#!/bin/bash

curl -X GET \
  -H "Content-Type: application/json" \
  -H "x-ha-access: $HA_KEY" \
  $HA_URL/api/stream
