#!/usr/bin/env bash

uwsgi --socket 127.0.0.1:5001 \
    --protocol=http \
    --http-chunked-input \
    -w mixmatch.wsgi \
    --master \
    --processes 4 \
    --threads 2
