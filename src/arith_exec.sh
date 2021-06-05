#!/bin/bash
# PYTHON=/mnt/c/Python27/python.exe
PYTHON=/usr/bin/python
SCRIPT=$(readlink -f "${BASH_SOURCE[0]}")
SCRIPTPATH=$(dirname $(SCRIPT))
${PYTHON} ${SCRIPTPATH}/arithconvert.py $1 $2
