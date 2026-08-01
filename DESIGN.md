---
name: Workshop Finder
description: The card catalog of workshops at A*/A conferences — deadlines first.
colors:
  paper: "#e9dcc8"
  paper-deep: "#dccab0"
  card: "#fff8ee"
  rule: "#d4c4a8"
  rule-hover: "#b9a688"
  ink: "#1f1812"
  ink-soft: "#5c5143"
  terracotta: "#c2410c"
  terracotta-deep: "#9a3412"
  terracotta-wash: "#f0d5c4"
  olive: "#3f6212"
  olive-wash: "#d9e4c8"
  graphite: "#8a7f6c"
  chip: "#e5d6bf"
  bar: "#2c2218"
  status-closing-bg: "#fce8e0"
  status-open-bg: "#e8f0dc"
  status-tba-bg: "#ebe4d6"
typography:
  display:
    fontFamily: "Zilla Slab, Georgia, serif"
    fontSize: "clamp(2.4rem, 6vw, 3.75rem)"
    fontWeight: 600
    lineHeight: 1.02
    letterSpacing: "-0.025em"
  empty-title:
    fontFamily: "Zilla Slab, Georgia, serif"
    fontSize: "1.4rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "normal"
  card-title:
    fontFamily: "Zilla Slab, Georgia, serif"
    fontSize: "1.2rem"
    fontWeight: 600
    lineHeight: 1.28
    letterSpacing: "-0.015em"
  body:
    fontFamily: "Atkinson Hyperlegible, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  search:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "1.05rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
  status:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
  option:
    fontFamily: "Atkinson Hyperlegible, system-ui, sans-serif"
    fontSize: "0.88rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
  meta:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "0.8rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
  label:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "0.78rem"
    fontWeight: 700
    lineHeight: 1.45
    letterSpacing: "0.09em"
  ledger:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "0.76rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
  count:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "0.75rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
  conf:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "0.74rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0.05em"
  chip:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "0.72rem"
    fontWeight: 700
    lineHeight: 1.5
    letterSpacing: "0.09em"
  key:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "0.68rem"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "0.07em"
  stamp-sub:
    fontFamily: "Courier Prime, Courier New, monospace"
    fontSize: "0.62rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0.1em"
rounded:
  none: "0"
  focus: "2px"
  sm: "4px"
  md: "6px"
  lg: "8px"
  xl: "10px"
  2xl: "12px"
  3xl: "14px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "40px"
components:
  catalog-card:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    rounded: "{rounded.2xl}"
    padding: "18px 20px 16px"
  deadline-stamp:
    textColor: "{colors.terracotta}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "6px 10px"
  drawer-option-active:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.card}"
    rounded: "{rounded.md}"
    padding: "6px 8px"
  status-chip:
    backgroundColor: "{colors.status-closing-bg}"
    textColor: "{colors.terracotta}"
    typography: "{typography.chip}"
    rounded: "{rounded.lg}"
    padding: "6px 12px"
---

# Design System: Workshop Finder

## 1. Overview

**Creative North Star: "The warm archive"**

Workshop Finder is a deadline-first Operate catalog on warm paper: cream cards
stamped with rank and submission status. Atmosphere is richer peach-and-ink — never
flat white, never green baize, never mustard brass. Researchers land with a topic,
scan closing stamps, and leave to the CFP.

**Key Characteristics:**
- Warm paper canvas with terracotta wash; cream elevated cards
- Terracotta = urgency (closing, A*, links); olive = open; graphite = TBA
- Status chips in the tray head for one-click deadline filtering
- Courier Prime for every date, code, count, and stamp
- Ledger charts are secondary — collapsed by default

## 2. Colors

A warm, paper-first palette with decisive status color — not monochrome cream.

### Primary
- **Terracotta** (#c2410c / #9a3412): CLOSING, A*, links, focus, closing chips.
- **Terracotta wash** (#f0d5c4): Header and atmosphere.

### Secondary
- **Olive** (#3f6212) + **Olive wash** (#d9e4c8): OPEN stamps and chips.

### Neutral
- **Paper** (#e9dcc8) / **Paper deep** (#dccab0): Page ground.
- **Card** (#fff8ee): Elevated surfaces.
- **Ink** (#1f1812) / **Soft ink** (#5c5143): Text.
- **Rule / Chip / Graphite / Bar**: borders, tracks, TBA, chart fills.

### Named Rules
**The Two-Ink Rule.** Only terracotta and olive carry status; graphite marks TBA.
**The No-Hardware Rule.** No brass, mustard, or metallic pills.

## 3. Typography

**Display Font:** Zilla Slab · **Body:** Atkinson Hyperlegible · **Mono:** Courier Prime

### Hierarchy
- **Display** (600, clamp(2.4rem, 6vw, 3.75rem)): Nameplate only — full strength.
- **Card Title** (600, 1.2rem): Workshop names.
- **Body / Search / Label / Meta:** as frontmatter.

### Named Rules
**The Typewriter Rule.** Dates, deadlines, acronyms, counts, statuses → Courier Prime.

## 4. Elevation

Single soft warm shadow on cards and ledger. Drawers and search stay flat (border only).

### Shadow Vocabulary
- **Card rest** (`0 1px 2px rgba(31,24,18,.06), 0 14px 32px -16px rgba(31,24,18,.22)`)

## 5. Components

### Status chips
Tray-head toggles for Closing / Open / TBA — wash backgrounds, ink/terracotta text, pressed = ink fill.

### Cards
12–14px radius cream cards; stamp top-right as structured badge (not decorative float); rank stamp beside conference line.

### Drawers
Cream surfaces with soft wash; espresso caret; active rows ink-on-cream.

### Ledger
Secondary; terracotta-washed cream panel with relative-width bars.

## 6. Do's and Don'ts

### Do:
- **Do** keep terracotta exclusive to urgency.
- **Do** lead with search + status chips, then cards.
- **Do** show TBA only for still-upcoming hosts; never invent deadlines.

### Don't:
- **Don't** return green baize or mustard brass.
- **Don't** use color alone for status — always pair with text.
- **Don't** default the ledger open — Operate is deadline-first cards.
- **Don't** add kickers, side-tab borders, or icon+heading feature grids.
