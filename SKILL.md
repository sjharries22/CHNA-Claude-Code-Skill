---
name: chna
description: >-
  Read, extract, summarize, and compare Community Health Needs Assessment
  (CHNA) reports, and clone a previous report's brand, structure, and tone into
  a new branded Gamma deck. Use when the user provides one or more CHNA .docx
  files (or asks about community health needs, health indicators, prioritized
  needs, or implementation strategies) and wants the content extracted,
  summarized, compared, audited against IRS 501(r)(3), or rebuilt as a new
  brand-consistent report.
---

# CHNA Report Skill

This skill helps work with **Community Health Needs Assessments** — the
triennial reports that not-for-profit hospitals must publish under IRS
section 501(r)(3). It turns dense `.docx` reports into structured, queryable
text and supports extraction, summarization, cross-report comparison, and
compliance checks.

## When to use

- The user supplies one or more `.docx` CHNA files (or a folder of them).
- They ask to summarize, extract data from, compare, or audit CHNA reports.
- They ask about prioritized health needs, indicators, demographics,
  community input, or implementation strategies.

## Workflow

### 1. Extract the document(s)

Word files are not plain text. Always convert first with the bundled
extractor — it needs **no third-party packages**:

```bash
# Single report → Markdown on stdout
python3 scripts/extract_docx.py "REPORT.docx"

# Save to a working file
python3 scripts/extract_docx.py "REPORT.docx" -o /tmp/report.md

# Structured blocks (headings/paragraphs/tables) for programmatic use
python3 scripts/extract_docx.py "REPORT.docx" --json
```

For a folder of reports:

```bash
for f in *.docx; do
  python3 scripts/extract_docx.py "$f" -o "/tmp/$(basename "$f" .docx).md"
done
```

The extractor preserves heading hierarchy (as `#` levels) and renders Word
tables as Markdown tables, so health-indicator tables stay readable.

### 2. Read and locate the standard sections

CHNAs follow a recognizable structure. See `references/chna_guide.md` for the
full anatomy and the IRS-required elements. The high-value sections are
usually: community served / demographics, health indicator data,
**prioritized health needs**, community input, and the implementation
strategy.

### 3. Do the requested task

- **Summarize** — Lead with the prioritized health needs, then the evidence
  (key indicators vs. state/national benchmarks), the community input method,
  and the implementation strategy. Always cite the section/heading you drew
  from so the user can verify.
- **Extract data** — Pull indicator tables verbatim; never invent figures. If
  a number isn't in the document, say so rather than estimating.
- **Compare reports** (e.g. successive cycles, or hospital vs. county) — Align
  on prioritized needs and shared indicators, and call out what changed,
  what's new, and what dropped off.
- **Compliance check** — Verify the IRS 501(r)(3) required elements are
  present (see the checklist in `references/chna_guide.md`).

## Match a previous report (brand + structure + tone) → Gamma deck

When the goal is a **new** report that keeps a previous report's brand visuals,
section structure, and writing tone, parse the old report once into three
reusable artifacts, then generate a branded Gamma deck. Full details and the
exact Gamma `generate` parameters are in `references/gamma_pipeline.md`.

1. **Brand kit** — `scripts/extract_brand.py "PREV.docx" -o brand_profile.json --media-dir out/media`
   pulls the color palette, fonts, logo/media, header/footer, and heading
   styles from the `.docx` theme.
2. **Structure** — `scripts/extract_structure.py "PREV.docx" -o structure.json`
   produces a heading outline with each section classified against the CHNA
   anatomy (and flags expected sections that are missing).
3. **Tone** — extract the prose with `extract_docx.py`, read it, and write a
   short tone guide (voice, reading level, terminology, do/don't).
4. **Brand theme** — list Gamma themes with the `get_themes` tool and reuse the
   client's existing custom theme (e.g. "Metopio Theme"); cross-check it
   against `brand_profile.json`. Gamma can apply a theme but not create one —
   pixel-level fixes are a one-time edit in the Gamma editor.
5. **Generate** — assemble cards from `structure.json` using the blueprints in
   `components/card_blueprints.md`, written in the tone guide's voice, then call
   the Gamma `generate` tool with the brand theme. **Dry-run 2–3 cards first**
   and share the URL before producing the full deck.

## Guardrails

- This is data extraction and analysis, **not** medical or legal advice.
- Quote figures exactly as written; flag anything ambiguous or missing rather
  than filling gaps.
- CHNA reports are public documents, but treat any embedded personal stories
  or comments as sensitive — summarize, don't republish wholesale.

## Files

- `scripts/extract_docx.py` — dependency-free `.docx` → Markdown/JSON extractor.
- `scripts/extract_brand.py` — brand-kit extractor (palette, fonts, logo/media,
  header/footer, heading styles) → `brand_profile.json`.
- `scripts/extract_structure.py` — heading outline + CHNA section classifier
  → `structure.json`.
- `components/card_blueprints.md` — reusable Gamma card templates for a CHNA.
- `references/chna_guide.md` — CHNA anatomy, IRS-required elements, and a
  compliance checklist.
- `references/gamma_pipeline.md` — how to turn a parsed report into a branded
  Gamma deck.
