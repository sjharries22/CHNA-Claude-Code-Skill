---
name: chna-ingest
description: Parse CHNA source documents (.docx, .zip-of-docx) into a single citation-ready sources.json. Use when the user provides CHNA input files and asks to prepare them for report generation, or before invoking the chna-generate skill.
---

# chna-ingest

Turn raw CHNA input files into a single, citation-ready `sources.json` that
`chna-generate` consumes. Parsing is deterministic (Python scripts);
classification and triage are delegated to sub-agents.

## Inputs

The user names a directory or file. Accept:

- A single `.docx`
- A `.zip` containing `.docx` files (or nested zips one level deep)
- A directory containing any mix of the above

Expected file kinds (names vary by organization):

- Secondary Data — quantitative health statistics
- Community Input / Summary — qualitative quotes organized by theme
- Demographics — population and demographic data
- Existing CHNA — previous CHNA reports (source of verbatim sections)
- Template reference — formatting examples

## Workflow

### 1. Resolve inputs

```bash
python skills/chna-ingest/scripts/unpack.py <user_path>
```

Emits a JSON list of `.docx` paths. Fail loudly if zero are found.

### 2. Extract each .docx in parallel

For each path returned by `unpack.py`, run:

```bash
python skills/chna-ingest/scripts/extract.py <docx> -o <out.json>
```

Run extractions in parallel using one general-purpose sub-agent per file
when there are more than three files; otherwise run sequentially. Each
extract emits chunks with `chunk_id`, `kind`, `heading_path`, and `text`.

### 3. Classify chunks (sub-agent fan-out)

Spawn one `general-purpose` sub-agent per file with the file's extracted
chunks. Each sub-agent returns the same chunks annotated with:

- `category`: one of `statistic`, `quote`, `methodology`, `verbatim_candidate`, `demographic`, `other`
- `themes`: list of health themes the chunk relates to (free-form strings; canonicalize in step 4)
- `disparity_dimensions`: list of demographic axes mentioned (e.g. `race`, `income`, `geography`) — empty if none
- `confidence`: `high` | `medium` | `low`

Brief the sub-agent that:

- It must NOT invent content. Categories and themes are derived strictly from the chunk's own text plus its `heading_path`.
- A quote is a community-member or stakeholder verbatim (often in quotation marks or attributed).
- A statistic must contain a number with a unit, percentage, rate, or count.
- A `verbatim_candidate` is a heading or paragraph that looks like a reusable methodology, acknowledgments, or boilerplate section.

### 4. Merge into sources.json

Combine all per-file outputs into `sources.json` at the user-specified
output location (default: alongside the inputs). Schema:

```json
{
  "generated_at": "<ISO timestamp>",
  "files": [
    {"source_file": "...", "source_path": "...", "chunk_count": N}
  ],
  "themes": ["..."],
  "chunks": [
    {
      "source_file": "...",
      "chunk_id": "...",
      "kind": "paragraph|heading|table_cell",
      "heading_path": ["..."],
      "category": "...",
      "themes": ["..."],
      "disparity_dimensions": ["..."],
      "confidence": "...",
      "text": "..."
    }
  ]
}
```

After the merge, canonicalize the theme list: collapse near-duplicates
(e.g. "Mental Health" / "Behavioral Health"), and write the canonical
list into the top-level `themes` field.

### 5. Report back

Print a short summary to the user:

- Number of files ingested
- Total chunks, broken down by category
- Canonical theme list
- Any files that produced zero chunks (likely empty or password-protected)
- Path to `sources.json`

## Constraints

- Never echo full document contents to the chat. CHNA documents may contain sensitive community health data. Summarize counts and category breakdowns instead.
- Never commit `sources.json` or any input file to the repo unless the user explicitly asks. They likely contain PHI-adjacent material.
- If `python-docx` is missing, instruct the user to run `pip install -r requirements.txt` from the repo root rather than installing globally.
