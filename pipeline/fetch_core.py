"""Fetch ICORE2026 A*/A conference rankings from portal.core.edu.au.

Outputs data/conferences.json: the prestige anchor for the whole dataset.
Primary path is the portal's one-shot CSV export (all 987 records in a single
request); the paginated HTML table parser is kept as a fallback.
"""

from __future__ import annotations

import csv
import io
import json
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = "https://portal.core.edu.au/conf-ranks/"
SOURCE = "ICORE2026"
WANTED_RANKS = {"A*", "A"}
MAX_PAGES = 8
OUT = Path(__file__).resolve().parent.parent / "data" / "conferences.json"

# ANZSRC 2020 Field of Research codes used by ICORE, plus the ICORE-added code.
FOR_FIELDS = {
    "4601": "Applied Computing",
    "4602": "Artificial Intelligence",
    "4603": "Computer Vision and Multimedia Computation",
    "4604": "Cybersecurity and Privacy",
    "4605": "Data Management and Data Science",
    "4606": "Distributed Computing and Systems Software",
    "4607": "Graphics, Augmented Reality and Games",
    "4608": "Human-Centred Computing",
    "4611": "Machine Learning",
    "4612": "Software Engineering",
    "4613": "Theory of Computation",
    "CSE": "Computer Systems Engineering",
}

HEADERS = {
    "User-Agent": "WorkshopFinderBot/1.0 (+https://github.com/aarush/workshop-finder; polite research scraper)"
}


def make_row(title: str, acronym: str, rank: str, for_code: str) -> dict:
    return {
        "title": title,
        "acronym": acronym,
        "source": SOURCE,
        "rank": rank,
        "dblp": None,
        "forCode": for_code,
        "field": FOR_FIELDS.get(for_code, for_code or "Unclassified"),
    }


def fetch_csv() -> list[dict]:
    """One-shot export: ID, Title, Acronym, Source, Rank, DBLP, PrimaryFoR, ..."""
    resp = requests.get(
        BASE,
        params={"search": "", "by": "all", "source": SOURCE, "do": "Export"},
        headers=HEADERS,
        timeout=60,
    )
    resp.raise_for_status()
    rows: list[dict] = []
    seen: set[str] = set()
    for parts in csv.reader(io.StringIO(resp.text)):
        if len(parts) < 7:
            continue
        _, title, acronym, source, rank, _dblp, for_code = parts[:7]
        if source != SOURCE or rank not in WANTED_RANKS or not acronym:
            continue
        key = acronym.upper()
        if key in seen:
            continue
        seen.add(key)
        rows.append(make_row(title.strip(), acronym.strip(), rank.strip(), for_code.strip()))
    return rows


def fetch_html_fallback() -> list[dict]:
    rows: list[dict] = []
    seen: set[str] = set()
    for page in range(1, MAX_PAGES + 1):
        resp = requests.get(
            BASE,
            params={"search": "", "by": "all", "source": SOURCE, "sort": "arank", "page": page},
            headers=HEADERS,
            timeout=30,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        page_rows: list[dict] = []
        if table:
            for tr in table.find_all("tr"):
                cells = tr.find_all("td")
                if len(cells) < 7:
                    continue
                title = cells[0].get_text(" ", strip=True)
                acronym = cells[1].get_text(" ", strip=True)
                rank = cells[3].get_text(" ", strip=True)
                dblp_link = cells[5].find("a")
                for_code = cells[6].get_text(" ", strip=True)
                if rank not in WANTED_RANKS or not acronym or not title:
                    continue
                row = make_row(title, acronym, rank, for_code)
                row["dblp"] = dblp_link["href"] if dblp_link and dblp_link.has_attr("href") else None
                page_rows.append(row)
        for r in page_rows:
            key = r["acronym"].upper()
            if key not in seen:
                seen.add(key)
                rows.append(r)
        print(f"page {page}: {len(page_rows)} A*/A (total {len(rows)})")
        if not page_rows:
            break
        time.sleep(1.5)
    return rows


def main() -> int:
    try:
        collected = fetch_csv()
        print(f"csv export: {len(collected)} A*/A conferences")
    except requests.RequestException as e:
        print(f"csv export failed ({e}); falling back to HTML pagination")
        collected = fetch_html_fallback()
    if not collected:
        collected = fetch_html_fallback()

    collected.sort(key=lambda r: (0 if r["rank"] == "A*" else 1, r["acronym"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"source": SOURCE, "conferences": collected}, indent=2) + "\n")
    print(f"wrote {len(collected)} A*/A conferences -> {OUT}")
    return 0 if collected else 1


if __name__ == "__main__":
    sys.exit(main())
