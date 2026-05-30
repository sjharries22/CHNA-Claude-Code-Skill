#!/usr/bin/env python3
"""Extract a brand kit + heading outline from a PDF CHNA report.

PDFs carry no theme XML, so brand cues are inferred from the rendered content
using PyMuPDF (``pip install pymupdf``):

  * fonts      -> tallied by characters drawn (dominant body + display fonts)
  * colors     -> text colors and vector fill colors (accent palette)
  * images     -> embedded images (the logo is usually the first/cover image)
  * headings   -> lines set noticeably larger than body text

Outputs a JSON brand+structure profile and (optionally) saves embedded images.

Usage:
    python3 extract_brand_pdf.py REPORT.pdf
    python3 extract_brand_pdf.py REPORT.pdf -o profile.json --image-dir out/img
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter

try:
    import fitz  # PyMuPDF
except ImportError:
    raise SystemExit("error: PyMuPDF is required -> pip install pymupdf")


def _hex_from_int(c: int) -> str:
    return f"#{(c >> 16) & 255:02X}{(c >> 8) & 255:02X}{c & 255:02X}"


def _hex_from_rgb01(rgb) -> str:
    r, g, b = (max(0, min(255, round(v * 255))) for v in rgb)
    return f"#{r:02X}{g:02X}{b:02X}"


def analyze(path: str, image_dir: str | None = None) -> dict:
    doc = fitz.open(path)

    font_chars: Counter[str] = Counter()
    size_chars: Counter[float] = Counter()
    text_colors: Counter[str] = Counter()
    fill_colors: Counter[str] = Counter()
    spans: list[tuple[int, float, str, str]] = []  # (page, size, font, text)

    for pno, page in enumerate(doc, start=1):
        data = page.get_text("dict")
        for block in data.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    n = len(text)
                    size = round(span.get("size", 0), 1)
                    font = span.get("font", "")
                    font_chars[font] += n
                    size_chars[size] += n
                    text_colors[_hex_from_int(span.get("color", 0))] += n
                    spans.append((pno, size, font, text))
        # vector fills give the accent/brand block colors
        for d in page.get_drawings():
            if d.get("fill"):
                fill_colors[_hex_from_rgb01(d["fill"])] += 1

    # Body size = the most common text size; headings are clearly larger.
    body_size = size_chars.most_common(1)[0][0] if size_chars else 0.0
    heading_threshold = body_size * 1.15
    headings: list[dict] = []
    seen: set[tuple[int, str]] = set()
    for pno, size, font, text in spans:
        if size >= heading_threshold and len(text) > 3 and len(text) < 120:
            key = (pno, text.lower())
            if key in seen:
                continue
            seen.add(key)
            headings.append({"page": pno, "size_pt": size, "font": font, "text": text})

    images: list[dict] = []
    if image_dir:
        os.makedirs(image_dir, exist_ok=True)
    seen_xref: set[int] = set()
    for pno, page in enumerate(doc, start=1):
        for img in page.get_images(full=True):
            xref = img[0]
            if xref in seen_xref:
                continue
            seen_xref.add(xref)
            entry = {"page": pno, "xref": xref, "width": img[2], "height": img[3]}
            if image_dir:
                try:
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n - pix.alpha >= 4:  # CMYK -> RGB
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    dest = os.path.join(image_dir, f"img_p{pno}_x{xref}.png")
                    pix.save(dest)
                    entry["saved_to"] = dest
                except Exception as exc:  # noqa: BLE001
                    entry["error"] = str(exc)
            images.append(entry)

    def top(counter: Counter, k: int) -> list[dict]:
        return [{"value": v, "weight": w} for v, w in counter.most_common(k)]

    return {
        "source": os.path.basename(path),
        "pages": doc.page_count,
        "page_size_pt": [round(doc[0].rect.width, 1), round(doc[0].rect.height, 1)],
        "body_size_pt": body_size,
        "fonts": top(font_chars, 8),
        "text_sizes_pt": top(size_chars, 8),
        "text_colors": top(text_colors, 8),
        "fill_colors": top(fill_colors, 8),
        "images": images,
        "headings": headings,
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Extract brand+structure from a PDF report.")
    ap.add_argument("pdf", help="path to the .pdf file")
    ap.add_argument("-o", "--output", help="write JSON here instead of stdout")
    ap.add_argument("--image-dir", help="also save embedded images (incl. logo) here")
    args = ap.parse_args(argv)

    profile = analyze(args.pdf, args.image_dir)
    payload = json.dumps(profile, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
        print(f"wrote profile to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(payload + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
