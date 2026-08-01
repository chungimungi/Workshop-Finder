#!/usr/bin/env bash
# Re-scrape all sources, rebuild the dataset, and place it where the static
# server serves it (dist/data/dataset.json). Runs inside the HF Space.
set -euo pipefail
cd /app
mkdir -p dist/data

python pipeline/fetch_core.py
python pipeline/fetch_openreview.py
python pipeline/backfill_deadlines.py
python pipeline/enrich_websites.py
python pipeline/build_dataset.py
python pipeline/extract_topics.py

echo "refresh: done -> $WF_DATASET_OUT"
