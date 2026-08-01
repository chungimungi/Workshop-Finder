---
title: Workshop Finder
emoji: 🗂️
colorFrom: gray
colorTo: black
sdk: static
pinned: false
license: apache-2.0
short_description: Every workshop at every A*/A conference — deadlines first.
---

# Workshop Finder

The card catalog of workshops at A*/A conferences. Search workshops across every
A* and A rated conference ([ICORE2026 rankings](https://portal.core.edu.au/conf-ranks/))
by topic, field of research, or keyword — submission deadlines first.

Conference deadline trackers cover main conferences; workshops are scattered
across OpenReview, conference sites, and individual CFP pages. Workshop Finder
unifies them in one prestige-anchored index that CI keeps fresh.

## How it works

```
pipeline/fetch_core.py        ICORE2026 portal  → data/conferences.json   (170 A*/A conferences)
pipeline/fetch_openreview.py  OpenReview API v2 → data/workshops_openreview.json
pipeline/enrich_websites.py   conference sites  → data/workshops_websites.json (curated fallback)
pipeline/build_dataset.py     merge + topics    → web/public/data/dataset.json
```

- **OpenReview** is the primary source: the openreview.net homepage embeds every
  active venue's group id (including workshops), and a per-conference prefix
  crawl catches upcoming workshops not yet listed. Deadlines come from each
  venue group's own content.
- **Conference websites** are the fallback for conferences that don't use
  OpenReview, driven by a curated map (`pipeline/conference_sites.json`).
- **Never fabricate**: unknown deadlines stay `null` and render as TBA.

### Run the pipeline

```bash
pip install -r pipeline/requirements.txt
bash pipeline/update.sh
```

### Continuous updates

GitHub is the source of truth; the app ships as a **free Hugging Face Static
Space**. A GitHub Action (`.github/workflows/update-data.yml`) runs the pipeline
on a daily schedule and on every push to `main`, builds the frontend, and pushes
the built site to the HF Static Space. Workshops that the keyword taxonomy can't
tag fall back to [LiquidAI/LFM2.5-230M](https://huggingface.co/LiquidAI/LFM2.5-230M),
a 230M edge model, so every workshop ships with topics. The Docker runtime in
`space/` and `Dockerfile` is kept as an optional PRO-only alternative that runs
the pipeline on the Space itself.

## Frontend

```bash
cd web
npm install
npm run dev
```

Vite + React + TypeScript, [Motion](https://motion.dev) for animation, fully
static — the site reads the pre-built `dataset.json`. Design system: *The
Catalog* (see `PRODUCT.md` and `DESIGN.md`), built with the
[Impeccable](https://impeccable.style/docs/) workflow.
