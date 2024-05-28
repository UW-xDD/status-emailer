#!/bin/bash
set -e

cd "$(dirname "$0")"

case $1 in
  24h | 7d ) ;;  # OK
  * ) echo "specify period: 24h or 7d" >&2
      exit 1;;
esac

jsons=(
    all-source.json
    all-source-"$1".json
    all-publisher-source.json
    all-publisher-source-"$1".json
)

for x in ${jsons[@]}; do
  ./runquery-search.sh "$x" > "out-$x"
done

./articlesummary.py "$1" ${jsons[@]/#/out-}

