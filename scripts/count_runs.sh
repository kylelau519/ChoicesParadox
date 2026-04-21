#!/usr/bin/env bash

count=$(find data/runs -type f | wc -l)
echo "${count} runs"
du -sh data
