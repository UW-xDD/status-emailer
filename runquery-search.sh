#!/bin/bash

if [[ -e $1 ]]; then
  set -- "@$1"
fi

[[ $ESBASE ]] || ESBASE=deepdive2000.chtc.wisc.edu/es/articles

export http_proxy=
curl -s -u $ES_USER:$ES_PASSWORD -X GET -H'Content-Type: application/json' \
     "$ESBASE/_search?pretty=true" -d "$1"

