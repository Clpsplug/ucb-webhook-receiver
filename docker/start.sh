#!/usr/bin/env bash

(
  cd "/opt/code" || {
    echo "cd FAILED!"
    exit 1
  }
  pipenv install
  pipenv run python ./main.py
)
