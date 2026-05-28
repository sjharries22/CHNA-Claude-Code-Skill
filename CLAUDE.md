# CLAUDE.md

Guidance for AI assistants (Claude Code and others) working in this repository.

## Repository status

This repository is in a bootstrapping phase. As of the latest commit, it contains only `.claude/settings.local.json` and this file. No application source, build scripts, tests, or dependency manifests exist yet. Update this document whenever new structure is added — do not let it drift behind reality.

## Project purpose

Based on the repository name (`CHNA-Claude-Code-Skill`) and the initial commit message ("Add CHNA Claude Code Skill configuration … permissions for processing DOCX files"), the intended deliverable is a **Claude Code Skill** for working with CHNA (Community Health Needs Assessment) documents in `.docx` form.

A Claude Code Skill is a packaged capability that Claude can invoke via the `Skill` tool. Skills live under a directory containing a `SKILL.md` (with YAML frontmatter describing name, description, and trigger conditions) plus any supporting scripts or assets. See the Claude Code docs (https://code.claude.com/docs) for the current skill packaging format before adding one to this repo.

Confirm scope with the user before assuming further details — none of the actual skill logic, prompt, or supporting code has been written yet.

## Repository layout

```
.
├── .claude/
│   └── settings.local.json   # Local Claude Code harness settings (gitignored-style; user-specific allow/deny lists)
├── .git/
└── CLAUDE.md                 # This file
```

When the skill itself is added, it will most likely live under a top-level directory (e.g. `skills/chna/` or similar) containing `SKILL.md` and any helper scripts. Update this section when that lands.

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

None configured yet. When tooling is added (Python `pyproject.toml`, Node `package.json`, a Makefile, etc.), document the canonical commands here — for example:

```
# Run tests
<command goes here>

# Lint / format
<command goes here>
```

Until then, there is nothing to run.
