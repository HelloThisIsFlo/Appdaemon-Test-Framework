#!/bin/bash

pytest-watch \
    --ext=.py,.yaml \
    -- \
    -s \
    --tb=line
