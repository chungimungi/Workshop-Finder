"""Assign topics to every workshop.

Strategy:
  1. Keyword taxonomy (fast, deterministic) — same as build_dataset.assign_topics.
  2. For any workshop still without topics, fall back to LiquidAI/LFM2.5-230M, a
     230M instruction-tuned edge model built for extraction. It picks 1-3 tags
     from the same taxonomy so the sidebar stays consistent.
  3. Final guarantee: a workshop with no topics after both steps inherits its
     host conference's field of research as a topic, so the dataset never
     ships an empty topics list.

Reads:  web/public/data/dataset.json
Writes: web/public/data/dataset.json (in place)

Run standalone:
    python pipeline/extract_topics.py
    python pipeline/extract_topics.py --no-llm   # keyword + field fallback only
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASET = Path(os.environ.get("WF_DATASET_OUT", ROOT / "web" / "public" / "data" / "dataset.json"))

# Must stay in sync with build_dataset.TOPIC_TAXONOMY so the sidebar's topic
# drawer and the LLM's output vocabulary match.
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
TAXONOMY_KEYS = list(TOPIC_TAXONOMY.keys())


def assign_topics_keyword(name: str, short_name: str | None = None) -> list[str]:
    hay = f" {name.lower()} {(short_name or '').lower()} "
    topics: list[str] = []
    for topic, keywords in TOPIC_TAXONOMY.items():
        if any(k in hay for k in keywords):
            topics.append(topic)
        if len(topics) == 3:
            break
    return topics


def _normalize(s: str) -> str:
    return re.sub(r"[^a-z&]+", " ", s.lower()).strip()


def match_taxonomy(raw: str) -> list[str]:
    """Map free-form LLM output to canonical taxonomy keys."""
    out: list[str] = []
    norm_keys = {_normalize(k): k for k in TAXONOMY_KEYS}
    for token in re.split(r"[,\n;|]", raw):
        t = _normalize(token)
        if not t:
            continue
        if t in norm_keys:
            out.append(norm_keys[t])
        else:
            # fuzzy: taxonomy key contained in the token or vice versa
            for nk, k in norm_keys.items():
                if nk and (nk in t or t in nk):
                    out.append(k)
                    break
        if len(out) == 3:
            break
    # dedupe preserving order
    seen: set[str] = set()
    return [o for o in out if not (o in seen or seen.add(o))]


_LLM = None


def load_llm():
    global _LLM
    if _LLM is not None:
        return _LLM
    from transformers import AutoModelForCausalLM, AutoTokenizer  # type: ignore
    model_id = "LiquidAI/LFM2.5-230M"
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto")
    _LLM = (tok, model)
    return _LLM


def llm_topics(name: str, short_name: str | None, field: str | None) -> list[str]:
    tok, model = load_llm()
    taxonomy_list = "\n".join(f"- {k}" for k in TAXONOMY_KEYS)
    ctx = f"Workshop name: {name}"
    if short_name and short_name != name:
        ctx += f"\nShort name: {short_name}"
    if field:
        ctx += f"\nField of research: {field}"
    user = (
        "You tag academic workshops with 1 to 3 topic labels drawn ONLY from this list:\n"
        f"{taxonomy_list}\n\n"
        f"{ctx}\n\n"
        "Reply with the topic labels separated by commas. Use only labels from the list. "
        "If unsure, pick the closest one. Do not add any other text."
    )
    messages = [{"role": "user", "content": user}]
    inputs = tok.apply_chat_template(messages, add_generation_prompt=True, return_tensors="pt")
    out = model.generate(inputs, max_new_tokens=48, do_sample=False)
    reply = tok.decode(out[0][inputs.shape[1]:], skip_special_tokens=True).strip()
    return match_taxonomy(reply)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true", help="skip the LLM fallback (keyword + field only)")
    args = ap.parse_args()

    data = json.loads(DATASET.read_text())
    workshops = data["workshops"]
    conf_field = {c["acronym"]: c.get("field") for c in data.get("conferences", [])}

    filled = 0
    llm_used = 0
    for w in workshops:
        if w.get("topics"):
            continue
        name = w["name"]
        short = w.get("shortName")
        field = conf_field.get(w["conference"])
        topics = assign_topics_keyword(name, short)
        if not topics and not args.no_llm:
            try:
                topics = llm_topics(name, short, field)
                llm_used += 1
            except Exception as e:
                print(f"  llm fallback failed for {w['conference']}/{name[:40]}: {e}", file=sys.stderr)
        # final guarantee: never ship empty topics — inherit the host field
        if not topics and field:
            topics = [field]
        if not topics:
            topics = ["AI for Science & Society"]
        w["topics"] = topics
        filled += 1

    DATASET.write_text(json.dumps(data, separators=(",", ":")) + "\n")
    print(f"extract_topics: filled {filled} of {len(workshops)} workshops (llm used for {llm_used})")
    still_empty = sum(1 for w in workshops if not w.get("topics"))
    print(f"extract_topics: {still_empty} workshops still without topics")
    return 0


if __name__ == "__main__":
    sys.exit(main())
