"""Fallback: scrape workshop listings from conference websites.

Not every A*/A conference uses OpenReview. For those, we keep a curated map of
each conference's official workshops page (pipeline/conference_sites.json) and
extract candidate workshop names + links with a generic heuristic: links whose
text or href mentions "workshop". Deadlines usually live on individual CFP
pages, so they stay null (shown as TBA) rather than being guessed.

Only conferences with no OpenReview coverage are attempted.
Output: data/workshops_websites.json
"""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SITES = ROOT / "pipeline" / "conference_sites.json"
OUT = DATA / "workshops_websites.json"
HEADERS = {"User-Agent": "WorkshopFinderBot/1.0 (+https://github.com/aarush/workshop-finder; polite research scraper)"}
DELAY = 1.0
MAX_PER_CONF = 40

WORKSHOP_WORD = re.compile(r"workshop", re.IGNORECASE)
DATE_WORD = re.compile(r"(deadline|due|submit|submission)", re.IGNORECASE)


def load_json(path: Path, default):
    return json.loads(path.read_text()) if path.exists() else default


def looks_like_listing(text: str) -> bool:
    """Skip nav junk: a real workshop link has a few words, not just 'Workshops'."""
    words = text.split()
    return 2 <= len(words) <= 25 and not DATE_WORD.search(text)


def scrape(conf: dict, url: str) -> list[dict]:
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    base_host = urlparse(url).netloc
    found: dict[str, dict] = {}
    for a in soup.find_all("a"):
        text = a.get_text(" ", strip=True)
        href = a.get("href") or ""
        if not text or not (WORKSHOP_WORD.search(text) or WORKSHOP_WORD.search(href)):
            continue
        if not looks_like_listing(text):
            continue
        full = urljoin(url, href)
        key = text.lower()
        if key not in found:
            found[key] = {
                "id": f"site:{conf['acronym']}:{key[:60]}",
                "name": text,
                "shortName": text,
                "workshopAcronym": text[:40],
                "conference": conf["acronym"],
                "year": None,
                "deadline": None,
                "deadlineRaw": None,
                "conferenceStart": None,
                "location": None,
                "website": full if urlparse(full).netloc == base_host or full.startswith("http") else url,
                "openreviewUrl": None,
                "url": full,
                "source": "website",
            }
        if len(found) >= MAX_PER_CONF:
            break
    return list(found.values())


def main() -> int:
    if not SITES.exists():
        print(f"no curated site map at {SITES} — skipping website enrichment")
        OUT.write_text(json.dumps({"workshops": []}) + "\n")
        return 0

    conferences = {c["acronym"]: c for c in load_json(DATA / "conferences.json", {"conferences": []})["conferences"]}
    covered = {w["conference"] for w in load_json(DATA / "workshops_openreview.json", {"workshops": []})["workshops"]}
    sites = load_json(SITES, {})

    workshops: list[dict] = []
    for acronym, info in sites.items():
        conf = conferences.get(acronym)
        url = (info or {}).get("url")
        if not conf or not url or acronym in covered:
            continue
        try:
            cards = scrape(conf, url)
            print(f"{acronym:10s} {len(cards):3d} workshop links from {url}")
            workshops += cards
        except requests.RequestException as e:
            print(f"{acronym:10s} FAILED {type(e).__name__} {url}")
        time.sleep(DELAY)

    OUT.write_text(json.dumps({"workshops": workshops}, indent=2) + "\n")
    print(f"wrote {len(workshops)} website-sourced workshops -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
