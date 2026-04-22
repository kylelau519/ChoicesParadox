#!/usr/bin/env bash

count=$(find data/runs -type f | wc -l)
echo "$count runs"
du -sh data

for d in data/runs/*; do
    count=$(find $d -type f | wc -l)
    echo ""
    echo "${count} runs in $d"
    du -sh $d
done
