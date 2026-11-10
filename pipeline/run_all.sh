#!/usr/bin/env bash
# Full refresh: download data, build snaps, grade 3rd/4th downs, model 4th-down decisions, rebuild index.html.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p work && cd work
python ../download.py ../data
python ../build.py ../data
python ../export.py
python ../fourth.py
python ../export4.py
python ../assemble.py
