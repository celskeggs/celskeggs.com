#!/bin/bash -e

python bloggen.py
appcfg.py update .
