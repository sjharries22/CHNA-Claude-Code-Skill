#!/usr/bin/env python3
"""Parse a full PDF CHNA into a structured content.json (PyMuPDF).

Classifies text by font size into numbered sections (largest), subsections,
body paragraphs, and bullet lists, and pulls tables with ``page.find_tables``.
The output matches the schema consumed by ``build_html_report.py`` so a parsed
report can be re-rendered, or used as the structural template for a new cycle.

Usage:
    python3 extract_pdf_content.py REPORT.pdf -o content.json
    python3 extract_pdf_content.py REPORT.pdf --outline      # headings only
"""
from __future__ import annotations

import argparse
import json
import re
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    raise SystemExit("error: PyMuPDF is required -> pip install pymupdf")

BULLET_RE = re.compile(r"^\s*[•●▪‣⁃\-\*]\s+")
NUM_SECTION_RE = re.compile(r"^\s*(\d+)\.\s+(.*)$")


def _line_text(line: dict) -> tuple[str, float, bool, bool]:
    """Return (text, max_size, is_bold, is_bullet) for a line of spans.

    A bullet line is one whose first glyph is drawn in a symbol font (the
    common way Word/InDesign render list bullets in a PDF)."""
    spans = line.get("spans", [])
    parts, size, bold = [], 0.0, False
    is_bullet = bool(spans) and "symbol" in spans[0].get("font", "").lower()
    for i, sp in enumerate(spans):
        if is_bullet and i == 0:
            continue  # drop the bullet glyph itself
        parts.append(sp.get("text", ""))
        size = max(size, sp.get("size", 0))
        font = sp.get("font", "").lower()
        if "bold" in font or "semibold" in font:
            bold = True
    return "".join(parts).strip(), round(size, 1), bold, is_bullet


def parse(path: str) -> dict:
    doc = fitz.open(path)

    # First pass: find the dominant (body) font size.
    from collections import Counter
    sizes: Counter[float] = Counter()
    for page in doc:
        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                text, size, _, _ = _line_text(line)
                if text:
                    sizes[size] += len(text)
    body = sizes.most_common(1)[0][0] if sizes else 10.0
    section_min = body * 2.0     # numbered section heads (e.g. 22pt vs 10pt body)
    sub_min = body * 1.35        # subsection heads (e.g. 15pt)

    title = doc.metadata.get("title") or doc[0].get_text().strip().split("\n")[0]
    sections: list[dict] = []
    cur: dict | None = None
    para: list[str] = []
    bullets: list[str] = []

    def flush_para():
        nonlocal para
        if para and cur is not None:
            text = " ".join(para).strip()
            if text:
                cur["blocks"].append({"type": "p", "text": text})
        para = []

    def flush_bullets():
        nonlocal bullets
        if bullets and cur is not None:
            cur["blocks"].append({"type": "ul", "items": bullets[:]})
        bullets = []

    for pno, page in enumerate(doc, start=1):
        # tables first, so we can skip their text rows
        table_rects = []
        try:
            for tbl in page.find_tables().tables:
                data = tbl.extract()
                table_rects.append(fitz.Rect(tbl.bbox))
                if cur is None:
                    continue
                rows = [[(c or "").strip().replace("\n", " ") for c in r] for r in data]
                rows = [r for r in rows if any(r)]
                # require a real grid: >=2 rows and >=2 columns
                if len(rows) >= 2 and max(len(r) for r in rows) >= 2:
                    flush_para(); flush_bullets()
                    cur["blocks"].append({"type": "table", "headers": rows[0], "rows": rows[1:]})
        except Exception:  # noqa: BLE001
            pass

        for block in page.get_text("dict").get("blocks", []):
            for line in block.get("lines", []):
                text, size, bold, is_bullet = _line_text(line)
                if not text:
                    continue
                # skip lines that fall inside an extracted table
                bbox = fitz.Rect(line["bbox"])
                if any(bbox.intersects(tr) for tr in table_rects):
                    continue

                m = NUM_SECTION_RE.match(text)
                if size >= section_min and m:
                    flush_para(); flush_bullets()
                    cur = {"number": m.group(1), "title": m.group(2).title(), "blocks": []}
                    sections.append(cur)
                elif size >= section_min:
                    # heading-size line with no number: treat as a continuation of
                    # the just-opened heading (multi-line titles), else a new section
                    if cur is not None and not cur["blocks"]:
                        cur["title"] = (cur["title"] + " " + text.title()).strip()
                    else:
                        flush_para(); flush_bullets()
                        cur = {"number": None, "title": text.title(), "blocks": []}
                        sections.append(cur)
                elif is_bullet and cur is not None:
                    flush_para()
                    if text:
                        bullets.append(text)
                elif size >= sub_min and bold and cur is not None:
                    flush_para(); flush_bullets()
                    cur["blocks"].append({"type": "h3", "text": text})
                elif BULLET_RE.match(text):
                    flush_para()
                    bullets.append(BULLET_RE.sub("", text).strip())
                else:
                    flush_bullets()
                    para.append(text)
        # paragraphs don't span pages cleanly; flush at page end
        flush_para(); flush_bullets()

    flush_para(); flush_bullets()
    return {"title": title, "subtitle": "", "sections": sections}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Parse a full PDF CHNA into content.json.")
    ap.add_argument("pdf")
    ap.add_argument("-o", "--output")
    ap.add_argument("--outline", action="store_true", help="print section titles only")
    args = ap.parse_args(argv)

    content = parse(args.pdf)
    if args.outline:
        for s in content["sections"]:
            num = f"{s['number']}. " if s["number"] else ""
            nblk = len(s["blocks"])
            print(f"{num}{s['title']}  ({nblk} blocks)")
        return 0

    payload = json.dumps(content, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
        print(f"wrote {len(content['sections'])} sections to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(payload + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
