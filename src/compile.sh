#!/bin/bash
# PYTHON=/mnt/c/Python27/python.exe
PYTHON=/usr/bin/python
SCRIPT=$(readlink -f "${BASH_SOURCE[0]}")
SCRIPTPATH=$(dirname $(SCRIPT))
${PYTHON} ${SCRIPTPATH}/vercomp.py $1 --arith ${1}.arith --bit-width 64 --ignore-overflow True --cpparg _Ibuild/ _DPARAM=0 _DBIT_WIDTH=64
