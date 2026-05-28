# CHNA Claude Code Skill

A [Claude Code Skill](https://code.claude.com/docs) for working with
**Community Health Needs Assessment (CHNA)** reports — the triennial reports
that not-for-profit U.S. hospitals must publish under IRS §501(r)(3).

The skill extracts text and tables from CHNA `.docx` files and helps
summarize them, compare reports across cycles, and check them against the
IRS-required elements.

## Contents

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Skill definition and workflow Claude follows |
| `scripts/extract_docx.py` | Dependency-free `.docx` → Markdown/JSON extractor |
| `references/chna_guide.md` | CHNA anatomy, IRS requirements, compliance checklist |

## Quick start

```bash
# Extract a report to Markdown
python3 scripts/extract_docx.py "MyHospital-CHNA-2024.docx"

# Or save it and emit structured JSON
python3 scripts/extract_docx.py "MyHospital-CHNA-2024.docx" -o report.md
python3 scripts/extract_docx.py "MyHospital-CHNA-2024.docx" --json
```

The extractor uses only the Python standard library, so no `pip install` is
required.

## Using it as a skill

Place this directory where Claude Code discovers skills (e.g. a
`.claude/skills/chna/` folder in your project, or your personal skills
directory), then ask Claude to summarize, compare, or audit your CHNA `.docx`
files.
