#!/usr/bin/env python3
"""Extract a reusable structure outline from a CHNA .docx (no third-party deps).

Reads the heading hierarchy, classifies each heading against the standard CHNA
section types, and emits a ``structure.json`` outline that can seed the cards
of a new Gamma deck so the new report follows the previous report's flow.

Reuses the heading detection from ``extract_docx.py``.

Usage:
    python3 extract_structure.py REPORT.docx                 # JSON to stdout
    python3 extract_structure.py REPORT.docx -o structure.json
    python3 extract_structure.py REPORT.docx --markdown      # human-readable outline
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_docx import extract  # noqa: E402  (local import after path tweak)

# Section type -> keywords that identify it (matched case-insensitively).
SECTION_TYPES: dict[str, list[str]] = {
    "executive_summary": ["executive summary", "summary of findings", "key findings"],
    "introduction": ["introduction", "purpose", "background", "about"],
    "community_description": ["community served", "community description", "service area",
                              "demographic", "population"],
    "methodology": ["methodology", "methods", "approach", "data sources", "process"],
    "secondary_data": ["secondary data", "health indicators", "health status", "data profile"],
    "primary_data": ["primary data", "community input", "survey", "focus group",
                     "key informant", "interviews", "listening"],
    "prioritized_needs": ["prioritized", "priority", "significant health needs",
                          "identified needs", "health priorities"],
    "resources": ["resources", "assets", "community resources", "existing resources"],
    "implementation": ["implementation", "strategy", "action plan", "next steps", "goals"],
    "prior_evaluation": ["evaluation of", "prior chna", "previous chna", "progress",
                         "impact of", "prior assessment"],
    "appendix": ["appendix", "appendices", "references", "acknowledg", "glossary"],
}


def classify(text: str) -> str:
    low = text.lower()
    for section_type, keywords in SECTION_TYPES.items():
        if any(kw in low for kw in keywords):
            return section_type
    return "other"


def build_outline(blocks: list[dict]) -> list[dict]:
    """Turn heading blocks into a nested outline with classified section types."""
    headings = [b for b in blocks if b["type"] == "heading"]
    root: list[dict] = []
    stack: list[tuple[int, dict]] = []  # (level, node)
    for h in headings:
        node = {
            "title": h["text"],
            "level": h["level"],
            "section_type": classify(h["text"]),
            "children": [],
        }
        while stack and stack[-1][0] >= h["level"]:
            stack.pop()
        if stack:
            stack[-1][1]["children"].append(node)
        else:
            root.append(node)
        stack.append((h["level"], node))
    return root


def summarize(outline: list[dict]) -> dict:
    """Count blocks and which CHNA section types were detected."""
    found: dict[str, int] = {}

    def walk(nodes: list[dict]) -> int:
        count = 0
        for n in nodes:
            count += 1
            found[n["section_type"]] = found.get(n["section_type"], 0) + 1
            count += walk(n["children"])
        return count

    total = walk(outline)
    expected = set(SECTION_TYPES) - {"appendix"}
    return {
        "total_headings": total,
        "section_types_found": found,
        "expected_sections_missing": sorted(expected - set(found)),
    }


def to_markdown(outline: list[dict], depth: int = 0) -> str:
    lines: list[str] = []
    for n in outline:
        bullet = "  " * depth + f"- {n['title']}  _({n['section_type']})_"
        lines.append(bullet)
        if n["children"]:
            lines.append(to_markdown(n["children"], depth + 1))
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Extract a CHNA structure outline from a .docx.")
    ap.add_argument("docx", help="path to the .docx file")
    ap.add_argument("-o", "--output", help="write JSON to this file instead of stdout")
    ap.add_argument("--markdown", action="store_true", help="emit a human-readable outline")
    args = ap.parse_args(argv)

    blocks = extract(args.docx)
    outline = build_outline(blocks)

    if args.markdown:
        out = to_markdown(outline) + "\n"
    else:
        out = json.dumps(
            {"outline": outline, "summary": summarize(outline)},
            indent=2, ensure_ascii=False,
        ) + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(out)
        print(f"wrote structure to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
