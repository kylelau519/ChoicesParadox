#!/usr/bin/env bash

python3 -m unittest discover -v -s run_preprocessor/tests -t .
python3 -m unittest discover -v -s stat_analysis/tests -t .
