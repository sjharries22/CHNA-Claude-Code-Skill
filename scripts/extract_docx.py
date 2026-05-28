#!/usr/bin/env python3
"""Extract readable text and tables from a .docx file without third-party deps.

A .docx is a ZIP archive whose main content lives in ``word/document.xml``.
This script walks that XML in document order and emits:

  * paragraphs as plain text (headings prefixed with ``#`` markers when a
    heading style is detected)
  * tables rendered as GitHub-flavored Markdown

Usage:
    python3 extract_docx.py REPORT.docx                # text to stdout
    python3 extract_docx.py REPORT.docx -o out.md      # text to a file
    python3 extract_docx.py REPORT.docx --json         # structured JSON

Designed for Community Health Needs Assessment (CHNA) reports, but works on
any Word document.
"""
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from xml.etree import ElementTree as ET

# WordprocessingML namespace
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _qn(tag: str) -> str:
    return f"{W}{tag}"


def _paragraph_text(p: ET.Element) -> str:
    """Concatenate all text runs in a paragraph, honoring tabs and breaks."""
    parts: list[str] = []
    for node in p.iter():
        tag = node.tag
        if tag == _qn("t"):
            parts.append(node.text or "")
        elif tag == _qn("tab"):
            parts.append("\t")
        elif tag in (_qn("br"), _qn("cr")):
            parts.append("\n")
    return "".join(parts).strip()


def _heading_level(p: ET.Element) -> int | None:
    """Return heading depth (1-9) if the paragraph uses a Heading style."""
    ppr = p.find(_qn("pPr"))
    if ppr is None:
        return None
    style = ppr.find(_qn("pStyle"))
    if style is None:
        return None
    val = style.get(_qn("val"), "")
    low = val.lower()
    if low.startswith("heading"):
        digits = "".join(ch for ch in val if ch.isdigit())
        return int(digits) if digits else 1
    if low in ("title",):
        return 1
    return None


def _table_to_markdown(tbl: ET.Element) -> str:
    rows: list[list[str]] = []
    for tr in tbl.findall(_qn("tr")):
        cells: list[str] = []
        for tc in tr.findall(_qn("tc")):
            cell_text = " ".join(
                _paragraph_text(p) for p in tc.findall(_qn("p"))
            ).strip()
            cells.append(cell_text.replace("|", "\\|").replace("\n", " "))
        if cells:
            rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    lines = ["| " + " | ".join(rows[0]) + " |"]
    lines.append("| " + " | ".join(["---"] * width) + " |")
    for r in rows[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


def extract(path: str) -> list[dict]:
    """Return an ordered list of blocks: {type, level?, text|markdown}."""
    try:
        with zipfile.ZipFile(path) as zf:
            with zf.open("word/document.xml") as fh:
                tree = ET.parse(fh)
    except (zipfile.BadZipFile, KeyError) as exc:
        raise SystemExit(f"error: not a readable .docx file ({path}): {exc}")

    body = tree.getroot().find(_qn("body"))
    if body is None:
        return []

    blocks: list[dict] = []
    for child in body:
        if child.tag == _qn("p"):
            text = _paragraph_text(child)
            if not text:
                continue
            level = _heading_level(child)
            if level:
                blocks.append({"type": "heading", "level": level, "text": text})
            else:
                blocks.append({"type": "paragraph", "text": text})
        elif child.tag == _qn("tbl"):
            md = _table_to_markdown(child)
            if md:
                blocks.append({"type": "table", "markdown": md})
    return blocks


def blocks_to_markdown(blocks: list[dict]) -> str:
    out: list[str] = []
    for b in blocks:
        if b["type"] == "heading":
            out.append("#" * min(b["level"], 6) + " " + b["text"])
        elif b["type"] == "paragraph":
            out.append(b["text"])
        elif b["type"] == "table":
            out.append(b["markdown"])
    return "\n\n".join(out) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Extract text/tables from a .docx file.")
    ap.add_argument("docx", help="path to the .docx file")
    ap.add_argument("-o", "--output", help="write output to this file instead of stdout")
    ap.add_argument("--json", action="store_true", help="emit structured JSON blocks")
    args = ap.parse_args(argv)

    blocks = extract(args.docx)
    payload = json.dumps(blocks, indent=2, ensure_ascii=False) if args.json else blocks_to_markdown(blocks)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(payload)
        print(f"wrote {len(blocks)} blocks to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
