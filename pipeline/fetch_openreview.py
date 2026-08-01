"""Fetch workshops at A*/A conferences from OpenReview.

Two discovery channels, unioned:
1. The openreview.net homepage embeds every active venue's group id, including
   workshops. One request yields the live "what's on now" set.
2. A prefix crawl per A*/A conference over known OpenReview domain families,
   which also catches upcoming workshops not yet listed as active.

For each workshop venue group we read title, website, location, dates, and
parse the submission deadline from the group's content. Output:
data/workshops_openreview.json
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CONFERENCES_JSON = ROOT / "data" / "conferences.json"
OUT = ROOT / "data" / "workshops_openreview.json"

API = "https://api2.openreview.net"
HOMEPAGE = "https://openreview.net/"
HEADERS = {"User-Agent": "WorkshopFinderBot/1.0 (+https://github.com/aarush/workshop-finder; polite research scraper)"}
DELAY = 0.25
YEARS = ("2026", "2027")

# Aliases from OpenReview id tokens to ICORE acronyms.
ACRONYM_ALIASES = {
    "IJCAI-ECAI": "IJCAI",
    "MM": "ACMMM",
    "NIPS": "NeurIPS",
    "SIGMOD": "SIGMOD",
}

# Extra prefix templates tried (with {yr}) after the generic families, for
# conferences whose OpenReview domain does not derive from the acronym.
EXTRA_PREFIXES = {
    "IJCAI": ["ijcai.org/IJCAI/{yr}", "IJCAI-ECAI/{yr}"],
}

GENERIC_PREFIXES = [
    "{ac}.cc/{yr}",
    "thecvf.com/{ac}/{yr}",
    "aclweb.org/{ac}/{yr}",
    "ACM.org/{ac}/{yr}",
    "{ac}.org/{yr}",
    "{ac}/{yr}",
]

VENUE_ID_RE = re.compile(r"([A-Za-z0-9_.-]+(?:\.[A-Za-z0-9_-]+)?(?:/[A-Za-z0-9_.-]+)?/\d{4}/Workshop(?:/[A-Za-z0-9_-]+)?)")
DATE_RE = re.compile(
    r"Submission Deadline:\s*([A-Za-z]{3}\s+\d{1,2}\s+\d{4}(?:\s+\d{1,2}:\d{2}(?:AM|PM))?[^,]*)",
    re.IGNORECASE,
)


def load_conferences() -> dict[str, dict]:
    data = json.loads(CONFERENCES_JSON.read_text())
    by_acronym = {}
    for c in data["conferences"]:
        by_acronym[c["acronym"].upper()] = c
    return by_acronym


def acronym_for_venue(venue_base: str, known: dict[str, dict]) -> str | None:
    """Map 'thecvf.com/CVPR/2026' or 'ACM.org/CHI/2026' or 'NeurIPS.cc/2026' to an ICORE acronym."""
    parts = venue_base.split("/")
    candidates = []
    if len(parts) == 2:  # NeurIPS.cc/2026, EMNLP/2026, IJCAI-ECAI/2026
        candidates.append(parts[0].split(".")[0])
    elif len(parts) == 3:  # thecvf.com/CVPR/2026, ACM.org/CHI/2026, ijcai.org/IJCAI/2026
        candidates.append(parts[1])
        candidates.append(parts[0].split(".")[0])
    for cand in candidates:
        cand = ACRONYM_ALIASES.get(cand, cand)
        if cand.upper() in known:
            return known[cand.upper()]["acronym"]
    return None


def homepage_workshop_ids() -> list[str]:
    resp = requests.get(HOMEPAGE, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    ids = {m.group(1) for m in VENUE_ID_RE.finditer(resp.text)}
    # keep only the workshop venue root (no deeper subgroups like /Authors)
    return sorted(i for i in ids if i.rsplit("/Workshop", 1)[-1].count("/") <= 1)


def get_groups(params: dict, retries: int = 2) -> list[dict]:
    """Query /groups with retries — the API intermittently returns empty/error."""
    for attempt in range(retries + 1):
        try:
            r = requests.get(f"{API}/groups", params=params, headers=HEADERS, timeout=25)
            if r.status_code == 200:
                groups = r.json().get("groups", [])
                if groups or attempt == retries:
                    return groups
        except requests.RequestException:
            if attempt == retries:
                return []
        time.sleep(1.0 + attempt)
    return []


def crawl_prefixes(known: dict[str, dict], already: set[str]) -> list[str]:
    """Prefix-crawl every A*/A conference and union with homepage actives —
    the homepage lists only active venues, so covered conferences can still
    hide upcoming or recently-closed workshops (CVPR: 19 active vs 113 total)."""
    found: list[str] = []
    for conf in known.values():
        ac = conf["acronym"]
        templates = [t.format(ac=ac, yr="{yr}") for t in GENERIC_PREFIXES]
        templates += EXTRA_PREFIXES.get(ac, [])
        hits_for_conf: list[str] = []
        for yr in YEARS:
            for tpl in templates:
                prefix = tpl.format(yr=yr) + "/Workshop"
                groups = get_groups({"prefix": prefix, "limit": 1000})
                tops = [g["id"] for g in groups if g["id"].count("/") == prefix.count("/") + 1]
                if tops:
                    hits_for_conf.extend(tops)
                    break  # first working domain wins for this year
                time.sleep(DELAY)
            if hits_for_conf:
                break  # found a year for this conference
        new = [h for h in hits_for_conf if h not in already]
        if hits_for_conf:
            print(f"  prefix crawl: {ac} -> {len(hits_for_conf)} workshops ({len(new)} beyond homepage)")
            found.extend(hits_for_conf)
    return found


def parse_date_string(raw: str) -> str | None:
    raw = raw.strip().replace("UTC-0", "+0000").replace("UTC", "+0000")
    for fmt in ("%b %d %Y %I:%M%p %z", "%b %d %Y %H:%M %z", "%b %d %Y %I:%M%p", "%b %d %Y"):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            continue
    return None


def content_value(content: dict, *keys: str) -> str | None:
    for k in keys:
        v = content.get(k)
        if isinstance(v, dict) and isinstance(v.get("value"), str) and v["value"].strip():
            return v["value"].strip()
    return None


def fetch_venue_details(venue_ids: list[str], known: dict[str, dict]) -> list[dict]:
    workshops = []
    for i, vid in enumerate(sorted(set(venue_ids))):
        base, _, tail = vid.partition("/Workshop/")
        conf_acronym = acronym_for_venue(base, known)
        if not conf_acronym:
            continue
        year_m = re.search(r"/(\d{4})/", vid)
        groups = get_groups({"id": vid})
        time.sleep(DELAY)
        if not groups:
            continue
        content = groups[0].get("content") or {}

        deadline = None
        date_blob = content_value(content, "date") or ""
        m = DATE_RE.search(date_blob)
        if m:
            deadline = parse_date_string(m.group(1))
        if not deadline:
            deadline = parse_date_string(content_value(content, "submission_deadline") or "")

        workshops.append(
            {
                "id": vid,
                "name": content_value(content, "title") or tail.replace("_", " "),
                "shortName": content_value(content, "subtitle") or tail.replace("_", " "),
                "workshopAcronym": tail,
                "conference": conf_acronym,
                "year": int(year_m.group(1)) if year_m else None,
                "openreviewUrl": f"https://openreview.net/group?id={vid}",
                "website": content_value(content, "website"),
                "location": content_value(content, "location"),
                "conferenceStart": parse_date_string(content_value(content, "start_date") or ""),
                "deadline": deadline,
                "deadlineRaw": m.group(1).strip() if m else None,
                "source": "openreview",
            }
        )
        if (i + 1) % 50 == 0:
            print(f"  details: {i + 1}/{len(venue_ids)}")
    return workshops


def main() -> int:
    known = load_conferences()
    print("fetching openreview.net homepage for active workshop venues...")
    home_ids = homepage_workshop_ids()
    print(f"  homepage yielded {len(home_ids)} workshop venue ids")
    extra = crawl_prefixes(known, set(home_ids))
    all_ids = sorted(set(home_ids) | set(extra))
    print(f"fetching details for candidate venues (filtered to A*/A conferences)...")
    workshops = fetch_venue_details(all_ids, known)
    workshops.sort(key=lambda w: (w["conference"], w["workshopAcronym"]))
    OUT.write_text(json.dumps({"workshops": workshops}, indent=2) + "\n")
    confs = sorted({w["conference"] for w in workshops})
    print(f"wrote {len(workshops)} workshops across {len(confs)} A*/A conferences -> {OUT}")
    print("conferences covered:", ", ".join(confs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
