#! /bin/bash
echo "Running mz.py"
source ~/.virtualenvs/mz/bin/activate
cd "$(dirname "$0")"
python mz.py

