"""Merge pipeline outputs into the frontend dataset.

Inputs:  data/conferences.json, data/workshops_openreview.json,
         data/workshops_websites.json (optional)
Output:  web/public/data/dataset.json

Responsibilities: dedupe OpenReview track variants into one card per workshop,
assign topic tags from a keyword taxonomy, pick the best link per workshop,
and stamp freshness metadata. Never invents deadlines — missing stays null.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = Path(os.environ.get("WF_DATASET_OUT", ROOT / "web" / "public" / "data" / "dataset.json"))

TOPIC_TAXONOMY: dict[str, list[str]] = {
    "LLMs & Generative AI": ["llm", "large language", "generative", "genai", "foundation model", "language model"],
    "AI Agents": ["agent", "agentic", "tool use"],
    "Interpretability & XAI": ["interpretab", "explainab", "xai", "blackbox", "mechanistic", "transparency"],
    "Multimodal": ["multimodal", "multi-modal", "vision-language", "vlm", "multi modal"],
    "Computer Vision": ["computer vision", "image", "video", "3d", "segmentation", "object detection", "visual"],
    "Robotics & Embodied AI": ["robot", "manipulation", "embodied", "sim2real", "autonomous driv", "humanoid", "tactile"],
    "Reinforcement Learning": ["reinforcement", " rl ", "rlhf", "rlxf", "bandit", "control"],
    "ML Systems & Efficiency": ["efficient", "mlsys", "systems", "infrastructure", "edge", "quantiz", "distill", "spars", "on-device", "tinyml", "serving", "compiler"],
    "Safety, Alignment & Trust": ["safety", "align", "robust", "trustworthy", "privacy", "secur", "adversar", "guardrail", "fairness", "bias"],
    "Health & Bio": ["health", "medic", "bio", "clinical", "drug", "protein", "genom", "imaging", "surg"],
    "NLP & Linguistics": ["nlp", "linguist", "translation", "speech", "dialog", "parsing", "multiling", "low-resource", "summariz"],
    "Data, Graphs & Knowledge": ["data management", "database", "benchmark", "dataset", "data mining", "graph", "knowledge", "retriev", "rag"],
    "HCI & Interaction": ["hci", "interaction", "human-agent", "human-ai", "hri", "xr", "wearable", "ubiquitous", "mixed reality", "augmented reality"],
    "Reasoning, Planning & Theory": ["reasoning", "theory", "logic", "planning", "neurosymbolic", "neuro-symbolic", "math", "causal", "probabil", "uncertain", "optimiz"],
    "AI for Science & Society": ["science", "ai4s", "climate", "education", "social good", "ai4good", "policy", "globalsouth", "sustainab", "agricultur", "materials", "chemistry", "physics"],
    "Graphics & Multimedia": ["graphics", "rendering", "multimedia", "audio", "music", "animation", "affective"],
}

TRACK_SUFFIXES = re.compile(
    r"(_ARR_Commitment|_ARR|_Commitment|_Challenge|_Direct_Submission|_Direct|_Non-?archival(_Track)?|"
    r"_Non-proceeding(s|_Track)?|_Extended_Abstracts|_Position_Paper(s|_Track)?|_Short|_Full|_Findings|"
    r"_Proceedings(_Track)?|_Demonstration(_Paper)?(_Track)?|_Demo(nstration)?(_Track)?)$",
    re.IGNORECASE,
)


def base_key(workshop_acronym: str) -> str:
    return TRACK_SUFFIXES.sub("", workshop_acronym).strip("_- ").lower()


def richness(w: dict) -> int:
    return sum(bool(w.get(k)) for k in ("deadline", "website", "location", "conferenceStart"))


NAME_TRACK_NOISE = re.compile(
    r"\s*(--\s*ARR Commitment|\(Direct Submission\)|\(ARR Commitment\)|-\s*ARR Commitment|"
    r"\s*ARR Commitment|\(Non-?[Aa]rchival( Track)?\))\s*$",
    re.IGNORECASE,
)


def dedupe_tracks(workshops: list[dict]) -> list[dict]:
    """Collapse OpenReview track variants (ARR commitment, challenge…) into one card."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for w in workshops:
        groups.setdefault((w["conference"], base_key(w["workshopAcronym"])), []).append(w)
    merged: list[dict] = []
    for (conf, base), variants in groups.items():
        canonical = [v for v in variants if base_key(v["workshopAcronym"]) == v["workshopAcronym"].lower()]
        best = max(canonical or variants, key=richness)
        deadlines = sorted(v["deadline"] for v in variants if v.get("deadline"))
        if deadlines and not best.get("deadline"):
            now = datetime.now(timezone.utc).isoformat()
            upcoming = [d for d in deadlines if d >= now]
            best = {**best, "deadline": upcoming[0] if upcoming else deadlines[-1], "deadlineRaw": None}
        best = {**best, "name": NAME_TRACK_NOISE.sub("", best["name"])}
        merged.append(best)
    return merged


def assign_topics(name: str) -> list[str]:
    hay = f" {name.lower()} "
    topics: list[str] = []
    for topic, keywords in TOPIC_TAXONOMY.items():
        if any(k in hay for k in keywords):
            topics.append(topic)
        if len(topics) == 3:
            break
    return topics


def parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def is_upcoming(w: dict, now: datetime) -> bool:
    """Keep only workshops that are still actionable.

    Drop when the submission deadline has passed, or when the host conference
    has already started (e.g. AAAI 2026 in Jan — TBA workshops still leave).
    Past calendar years with no future deadline also leave.
    """
    deadline = parse_iso(w.get("deadline"))
    if deadline and deadline < now:
        return False
    conf_start = parse_iso(w.get("conferenceStart"))
    if conf_start and conf_start < now:
        return False
    year = w.get("year")
    if isinstance(year, int) and year < now.year and not deadline:
        return False
    return True


def main() -> int:
    conferences = json.loads((DATA / "conferences.json").read_text())["conferences"]
    by_acronym = {c["acronym"]: c for c in conferences}
    now = datetime.now(timezone.utc)

    workshops: list[dict] = []
    or_path = DATA / "workshops_openreview.json"
    if or_path.exists():
        workshops += json.loads(or_path.read_text())["workshops"]
    web_path = DATA / "workshops_websites.json"
    if web_path.exists():
        workshops += json.loads(web_path.read_text())["workshops"]

    workshops = dedupe_tracks(workshops)
    before = len(workshops)
    workshops = [w for w in workshops if is_upcoming(w, now)]
    print(f"upcoming filter: kept {len(workshops)} of {before} (dropped closed / past host conferences)")

    cards = []
    for w in workshops:
        conf = by_acronym.get(w["conference"])
        if not conf:
            continue  # workshop host slipped outside the A*/A list
        website = w.get("website")
        if website and not website.startswith(("http://", "https://")):
            website = "https://" + website.lstrip("/")
            w["website"] = website
        url = website or w.get("openreviewUrl") or w.get("url")
        cards.append(
            {
                "id": w["id"],
                "name": w["name"],
                "shortName": w.get("shortName") or w["name"],
                "workshopAcronym": w["workshopAcronym"],
                "conference": w["conference"],
                "year": w.get("year"),
                "deadline": w.get("deadline"),
                "deadlineRaw": w.get("deadlineRaw"),
                "conferenceStart": w.get("conferenceStart"),
                "location": w.get("location"),
                "website": w.get("website"),
                "openreviewUrl": w.get("openreviewUrl"),
                "url": url,
                "topics": assign_topics(f"{w['name']} {w.get('shortName') or ''}"),
                "source": w.get("source", "openreview"),
            }
        )

    cards.sort(key=lambda c: (c["conference"], c["workshopAcronym"]))
    used_conferences = sorted({c["conference"] for c in cards})
    conf_out = [
        {k: c[k] for k in ("acronym", "title", "rank", "field", "forCode", "dblp")}
        for c in conferences
        if c["acronym"] in used_conferences
    ]

    dataset = {
        "meta": {
            "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "workshopCount": len(cards),
            "conferenceCount": len(conf_out),
            "sources": ["OpenReview", "ICORE2026", "conference websites"],
        },
        "conferences": conf_out,
        "workshops": cards,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(dataset, separators=(",", ":")) + "\n")
    dated = sum(1 for c in cards if c["deadline"])
    print(f"dataset: {len(cards)} workshops ({dated} with deadlines) at {len(conf_out)} conferences -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
