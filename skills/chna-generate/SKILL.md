---
name: chna-generate
description: Generate a Community Health Needs Assessment (CHNA) report (.md + .txt) from a sources.json produced by chna-ingest plus a chna.config.yaml. Use when the user has ingested CHNA inputs and wants to produce the final report.
---

# chna-generate

Produce a CHNA report from `sources.json` (output of `chna-ingest`) and
`chna.config.yaml` (user-controlled selections). Every statistic and
quote in the output must trace to a chunk in `sources.json` — no
fabrication, no estimation.

## Required inputs

1. `sources.json` — produced by `chna-ingest`.
2. `chna.config.yaml` — see `config.example.yaml` for the schema. If
   missing, run the **config bootstrap** workflow below before
   generating anything.

## Config bootstrap (no config present)

When `chna.config.yaml` does not exist, use `AskUserQuestion` to collect:

1. **Verbatim sections** — show the user the list of `verbatim_candidate` chunks (heading + source_file) from `sources.json` and ask which to copy unchanged. Record the selected `chunk_id`s.
2. **Themes to include** — show the canonical theme list from `sources.json`. Ask which to include in the final report.
3. **Prioritized needs** — from the selected themes, ask which 2–3 are the prioritized health needs for implementation focus.
4. **Template overrides** — section header names, organization name, geographic scope, date placeholders.

Write answers to `chna.config.yaml` so the run is reproducible, then
continue.

## Workflow

### 1. Validate

- Load `sources.json` and `chna.config.yaml`.
- Confirm every `verbatim_chunk_id` in the config exists in `sources.json`. Abort with a clear error if any are missing.
- Confirm every `prioritized_need` is also in the `included_themes` list.

### 2. Render verbatim sections

For each `verbatim_chunk_id`, pull the chunk's `text` and any descendants under its `heading_path` from `sources.json` and emit them unchanged. Track the byte-for-byte output for the verbatim-guard check.

### 3. Draft significant-need sections (sub-agent fan-out)

For each theme in `included_themes`, spawn one `general-purpose`
sub-agent. Brief each sub-agent with:

- The theme name.
- The slice of `sources.json` chunks whose `themes` include this theme.
- The 5-section template at `templates/section.md`.
- The hard rule: every statistic and quote in the draft must cite a
  `{source_file, chunk_id}`. No paraphrased statistics without a
  citation. If a section cannot be supported by the available chunks,
  emit `N/A — Limited specific data available for [<geographic scope>]`
  rather than improvising.
- HIGHLIGHTED DISPARITIES requires comparative data across demographic
  groups. If `disparity_dimensions` is empty across the theme's chunks,
  state that explicitly and recommend data collection for future
  assessments.

Collect the drafted section blocks.

### 4. Citation auditor (sub-agent)

Spawn one `general-purpose` sub-agent with the full draft and
`sources.json`. Brief it to:

- Walk every numeric value, percentage, rate, and quoted string in the draft.
- Verify each maps to a chunk by `{source_file, chunk_id}` whose `text` contains the same value (allow whitespace and capitalization differences only).
- Return a list of `unsupported_claims` with location pointers. Do not autofix — return the list.

If the list is non-empty, the orchestrating skill must either rewrite
the offending passages (next sub-agent call) or strip them and replace
with `N/A`. Repeat until the auditor returns an empty list.

### 5. Verbatim guard (sub-agent)

Spawn one `general-purpose` sub-agent with the verbatim sections from
step 2 and the corresponding chunks from `sources.json`. Brief it to
return `ok` only if the rendered verbatim text matches the source
chunk text exactly (after normalizing line endings). Otherwise return
the diff. On a non-`ok` result, the orchestrating skill must
regenerate step 2 — never edit the output to "fix" verbatim drift.

### 6. Assemble and emit

Build the final report in this order (header names come from
`chna.config.yaml`):

1. Title block + date placeholders.
2. Verbatim sections in the order they appear in the config.
3. **Prioritized Health Needs** — list the 2–3 prioritized needs with a one-sentence rationale each, sourced from step 3 drafts.
4. **Significant Health Needs** — full 5-section block per theme (prioritized first, then the rest).
5. **Demographics** — descriptive section pulled from chunks with `category: demographic`. Never list demographics as a significant health need.
6. **Appendix: Data Sources** — render `templates/appendix.md` populated with the full citation log: for each cited chunk, output `{source_file} — {heading_path joined with > } — {chunk_id}`.

Write outputs:

- `<output_dir>/chna-report.md`
- `<output_dir>/chna-report.txt` — same content with markdown stripped (use Python's `markdown` if installed, otherwise a simple regex strip; the .txt is for Word/PDF import).

### 7. Report back

Print to the user:

- The two output paths.
- Theme count, prioritized-need list.
- Citation count and unsupported-claim count (should be zero).
- Verbatim guard result.
- Any sections that fell back to `N/A` and why.

## Constraints

- When the user asks "did you make up any data?", the answer is "No" because the citation auditor enforces it. If the auditor was ever skipped, say so and re-run it.
- Never commit `chna-report.*` to the repo unless the user explicitly asks. Output may contain PHI-adjacent content.
- Date placeholders use the format `[INSERT APPROVAL DATE]`, `[INSERT FISCAL YEAR]`, etc. — never invent dates.
- Geographic names come only from the config or chunk text — never guessed.
