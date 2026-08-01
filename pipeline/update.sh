#!/usr/bin/env bash
# Refill the catalog: re-scrape all sources and rebuild the frontend dataset.
set -euo pipefail
cd "$(dirname "$0")/.."

python3 pipeline/fetch_core.py
python3 pipeline/fetch_openreview.py
python3 pipeline/backfill_deadlines.py
python3 pipeline/enrich_websites.py
python3 pipeline/build_dataset.py
python3 pipeline/extract_topics.py
