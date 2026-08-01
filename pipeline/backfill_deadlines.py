"""Backfill missing deadlines from OpenReview Submission invitations.

Many venue groups leave content.date empty even when the Submission
invitation carries a machine-readable duedate (Unix ms). For every workshop
in data/workshops_openreview.json without a deadline, re-fetch its group for
content.submission_id, then fetch the invitation's duedate (expdate as
fallback). Updates the file in place. Never guesses — only copies real dates.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://api2.openreview.net"
HEADERS = {"User-Agent": "WorkshopFinderBot/1.0 (+https://github.com/aarush/workshop-finder)"}
DELAY = 0.25
PATH = Path(__file__).resolve().parent.parent / "data" / "workshops_openreview.json"


def get(url_params: dict, endpoint: str = "groups", retries: int = 2) -> list[dict]:
    for attempt in range(retries + 1):
        try:
            r = requests.get(f"{API}/{endpoint}", params=url_params, headers=HEADERS, timeout=25)
            if r.status_code == 200:
                data = r.json().get(endpoint, [])
                if data or attempt == retries:
                    return data
        except requests.RequestException:
            if attempt == retries:
                return []
        time.sleep(1.0 + attempt)
    return []


def ms_to_iso(ms: int | None) -> str | None:
    if not isinstance(ms, (int, float)):
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    data = json.loads(PATH.read_text())
    workshops = data["workshops"]
    undated = [w for w in workshops if not w.get("deadline")]
    print(f"{len(undated)} of {len(workshops)} workshops lack deadlines; backfilling...")

    filled = 0
    for i, w in enumerate(undated):
        groups = get({"id": w["id"]})
        time.sleep(DELAY)
        if not groups:
            continue
        content = groups[0].get("content") or {}
        submission_id = (content.get("submission_id") or {}).get("value")
        if not submission_id:
            continue
        invitations = get({"id": submission_id}, endpoint="invitations")
        time.sleep(DELAY)
        if not invitations:
            continue
        inv = invitations[0]
        iso = ms_to_iso(inv.get("duedate")) or ms_to_iso(inv.get("expdate"))
        if iso:
            w["deadline"] = iso
            w["deadlineRaw"] = None
            filled += 1
        if (i + 1) % 25 == 0:
            print(f"  {i + 1}/{len(undated)} checked, {filled} filled")

    PATH.write_text(json.dumps(data, indent=2) + "\n")
    print(f"backfilled {filled} deadlines -> {PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
