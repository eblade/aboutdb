#!/bin/bash -e
# Usage
#   $ ./scripts/run_tests.sh
# or
#   $ ./scripts/run_tests.sh --cov pycvodes --cov-report html
python -m pytest --pep8 --flakes -v $@
python -m doctest README.rst
