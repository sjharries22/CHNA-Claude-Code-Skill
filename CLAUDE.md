# CLAUDE.md

Guidance for AI assistants (Claude Code and others) working in this repository.

## Repository status

This repository ships a two-skill Claude Code Skill for producing Community Health Needs Assessment (CHNA) reports from `.docx` source documents. The skills are scaffolded and the deterministic parsing has been smoke-tested end-to-end against a synthetic `.docx`; no real CHNA inputs have been validated yet. Update this document whenever structure changes — do not let it drift behind reality.

## Project purpose

A **Claude Code Skill** for converting CHNA source files (existing CHNAs, community input, secondary data, demographics) into a standardized CHNA report. The pipeline is split into two skills so each half can be iterated on independently:

- `chna-ingest` — parses `.docx` (or `.zip` of `.docx`) inputs into a single citation-ready `sources.json`.
- `chna-generate` — consumes `sources.json` plus a user-controlled `chna.config.yaml` and produces `chna-report.md` + `chna-report.txt`.

Hard rule across both skills: **no fabricated data**. Every statistic and quote in the output must trace to a chunk in `sources.json`. The generator enforces this with a citation-auditor sub-agent before emitting the report. See `skills/chna-generate/SKILL.md` for the full workflow.

## Repository layout

```
.
├── .claude/
│   └── settings.local.json       # Local Claude Code harness settings (user-specific allow/deny lists)
├── skills/
│   ├── chna-ingest/
│   │   ├── SKILL.md              # Workflow instructions; invoked via the Skill tool
│   │   └── scripts/
│   │       ├── unpack.py         # Resolve .docx / .zip / dir → list of .docx paths
│   │       └── extract.py        # .docx → citation-ready chunk JSON
│   └── chna-generate/
│       ├── SKILL.md              # Workflow instructions; invoked via the Skill tool
│       ├── config.example.yaml   # Schema reference for chna.config.yaml
│       └── templates/
│           ├── section.md        # 5-section template per significant health need
│           └── appendix.md       # Data-source appendix template
├── requirements.txt              # python-docx, PyYAML
├── .git/
└── CLAUDE.md                     # This file
```

Outputs (`sources.json`, `chna.config.yaml`, `chna-report.*`) are NOT checked into the repo — they may contain PHI-adjacent material. Treat them as run-local artifacts.

## Local Claude Code settings

`.claude/settings.local.json` currently allow-lists two Bash patterns used to iterate `.docx` files:

```json
{
  "permissions": {
    "allow": [
      "Bash(for file in *.docx)",
      "Bash(do echo \"=== $file ===\")"
    ],
    "deny": [],
    "ask": []
  }
}
```

These are user-specific permission shortcuts so the harness doesn't prompt for those particular Bash invocations. Do not commit secrets, tokens, or machine-specific paths here. If you need allowlist entries that should apply to every contributor, move them to a checked-in `.claude/settings.json` instead of `settings.local.json`.

## Development workflow

### Branching

- Active development branch for this work: **`claude/claude-md-docs-aGdsB`** (the branch on which CLAUDE.md is being maintained).
- The default branch is `master`.
- Create feature branches from `master` (or the branch the user names explicitly). Do not push to `master` without an explicit request.

### Commits

- Follow the style established by the initial commit: a short imperative subject line, an optional body explaining *why*, and the Claude Code co-author trailer when the commit was generated with Claude Code's help.
- Keep commits focused. Don't bundle skill code, configuration changes, and docs into one commit if they can stand alone.

### Pushing

- Use `git push -u origin <branch-name>`.
- Only retry on network errors, with exponential backoff (2s, 4s, 8s, 16s) up to four attempts.
- Do **not** open a pull request unless the user explicitly asks for one.

### GitHub interactions

The remote execution environment exposes the GitHub MCP server (tools prefixed `mcp__github__`). There is no `gh` CLI. Use those MCP tools for PRs, issues, comments, CI status, etc. Tool access is scoped to `sjharries22/chna-claude-code-skill`; do not attempt cross-repo operations.

## Conventions for AI assistants

- **Verify before writing.** This repo is small enough that you can read everything before making changes. Do so — don't guess at structure.
- **Prefer editing over creating.** If a file already covers a concern, extend it rather than spawning a parallel one.
- **No speculative scaffolding.** Don't pre-create empty directories, placeholder modules, or "future" config files. Add structure when it's actually needed.
- **Keep this file current.** When you add real source code, dependency manifests, test commands, or skill packaging, update the relevant sections above in the same commit.
- **DOCX processing.** Any skill logic that opens `.docx` files should treat them as zipped XML (or use a vetted library like `python-docx`). Do not invent file formats. When iterating documents in shell, the allow-listed patterns in `.claude/settings.local.json` are already approved.
- **Secrets and PHI.** CHNA documents may contain sensitive community health data. Treat any sample document the user provides as confidential: don't echo full contents into commits, don't upload to third-party services, and don't include it in commit messages or PR descriptions.

## Build, test, lint

```bash
# Install Python dependencies (python-docx, PyYAML)
pip install -r requirements.txt

# Resolve an input path (file, zip, or directory) → JSON list of .docx paths
python3 skills/chna-ingest/scripts/unpack.py <path>

# Extract a single .docx to citation-ready JSON
python3 skills/chna-ingest/scripts/extract.py <path/to.docx> -o out.json
```

No test suite or linter is configured yet. When one is added (pytest, ruff, mypy, etc.), put the canonical commands here.

## Skill architecture notes

- **SKILL.md vs scripts.** Deterministic parsing lives in the Python scripts under `skills/chna-ingest/scripts/`. Judgment — classifying chunks, drafting sections, auditing citations — lives in `SKILL.md` instructions that orchestrate sub-agents.
- **Sub-agent fan-out.** `chna-generate` deliberately splits work across `general-purpose` sub-agents: one per prioritized health need (drafting), one citation auditor, one verbatim guard. This isolates each draft from the others and gives the auditor a clean comparison surface against `sources.json`.
- **Reproducibility.** `chna.config.yaml` is the single source of truth for user choices (verbatim sections, themes, prioritized needs, header overrides). Re-running `chna-generate` with the same config and the same `sources.json` should produce the same report.
- **Chunk IDs are stable.** `extract.py` derives `chunk_id` from paragraph index (`p:N`) or table coordinates (`t:T:R:C`). Don't break this format without updating both skills and any existing configs that reference them.
