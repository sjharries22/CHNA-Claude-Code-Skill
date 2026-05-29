#!/usr/bin/env python3
"""Extract a brand kit from a .docx file (no third-party deps).

A .docx is a ZIP archive. Brand assets live in predictable parts:

  * ``word/theme/theme1.xml``    -> color palette + font scheme
  * ``word/media/*``             -> logos and images
  * ``word/header*.xml``         -> header text (often the brand line)
  * ``word/footer*.xml``         -> footer text
  * ``word/styles.xml``          -> named heading styles (font/size/color)

This produces a ``brand_profile.json`` describing the palette, fonts, header/
footer text, and embedded media, and (optionally) saves the media files so a
logo can be reused on a Gamma cover card. The visual *reproduction* is meant
to be done by a Gamma theme; this kit documents the brand and feeds that setup.

Usage:
    python3 extract_brand.py REPORT.docx                      # JSON to stdout
    python3 extract_brand.py REPORT.docx -o brand_profile.json
    python3 extract_brand.py REPORT.docx --media-dir out/media  # also save logos
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
from xml.etree import ElementTree as ET

# DrawingML namespace (themes) and WordprocessingML namespace (styles/headers)
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Friendly names for the standard theme color slots.
COLOR_SLOTS = [
    "dk1", "lt1", "dk2", "lt2",
    "accent1", "accent2", "accent3", "accent4", "accent5", "accent6",
    "hlink", "folHlink",
]


def _color_value(slot: ET.Element) -> str | None:
    """A theme color slot holds either an srgbClr or a sysClr."""
    srgb = slot.find(f"{A}srgbClr")
    if srgb is not None and srgb.get("val"):
        return "#" + srgb.get("val").upper()
    sysclr = slot.find(f"{A}sysClr")
    if sysclr is not None and sysclr.get("lastClr"):
        return "#" + sysclr.get("lastClr").upper()
    return None


def _extract_theme(zf: zipfile.ZipFile) -> dict:
    palette: dict[str, str] = {}
    fonts: dict[str, str] = {}
    try:
        with zf.open("word/theme/theme1.xml") as fh:
            root = ET.parse(fh).getroot()
    except KeyError:
        return {"palette": palette, "fonts": fonts}

    clr_scheme = root.find(f".//{A}clrScheme")
    if clr_scheme is not None:
        for name in COLOR_SLOTS:
            slot = clr_scheme.find(f"{A}{name}")
            if slot is not None:
                val = _color_value(slot)
                if val:
                    palette[name] = val

    for role, tag in (("heading", "majorFont"), ("body", "minorFont")):
        node = root.find(f".//{A}{tag}/{A}latin")
        if node is not None and node.get("typeface"):
            fonts[role] = node.get("typeface")
    return {"palette": palette, "fonts": fonts}


def _xml_text(zf: zipfile.ZipFile, name: str) -> str:
    try:
        with zf.open(name) as fh:
            root = ET.parse(fh).getroot()
    except KeyError:
        return ""
    parts = [n.text or "" for n in root.iter(f"{W}t")]
    return " ".join(" ".join(parts).split()).strip()


def _extract_header_footer(zf: zipfile.ZipFile) -> dict:
    names = zf.namelist()
    headers = [
        _xml_text(zf, n)
        for n in sorted(names)
        if n.startswith("word/header") and n.endswith(".xml")
    ]
    footers = [
        _xml_text(zf, n)
        for n in sorted(names)
        if n.startswith("word/footer") and n.endswith(".xml")
    ]
    return {
        "headers": [h for h in headers if h],
        "footers": [f for f in footers if f],
    }


def _extract_media(zf: zipfile.ZipFile, media_dir: str | None) -> list[dict]:
    media: list[dict] = []
    for name in sorted(zf.namelist()):
        if not name.startswith("word/media/"):
            continue
        info = zf.getinfo(name)
        entry = {"name": os.path.basename(name), "bytes": info.file_size}
        if media_dir:
            os.makedirs(media_dir, exist_ok=True)
            dest = os.path.join(media_dir, os.path.basename(name))
            with zf.open(name) as src, open(dest, "wb") as out:
                out.write(src.read())
            entry["saved_to"] = dest
        media.append(entry)
    return media


def _extract_heading_styles(zf: zipfile.ZipFile) -> list[dict]:
    """Pull font/size/color for the named Heading styles in styles.xml."""
    try:
        with zf.open("word/styles.xml") as fh:
            root = ET.parse(fh).getroot()
    except KeyError:
        return []
    styles: list[dict] = []
    for style in root.findall(f"{W}style"):
        sid = style.get(f"{W}styleId", "")
        if not sid.lower().startswith(("heading", "title")):
            continue
        rpr = style.find(f"{W}rPr")
        entry: dict = {"style": sid}
        if rpr is not None:
            fonts = rpr.find(f"{W}rFonts")
            if fonts is not None and fonts.get(f"{W}ascii"):
                entry["font"] = fonts.get(f"{W}ascii")
            sz = rpr.find(f"{W}sz")
            if sz is not None and sz.get(f"{W}val"):
                # half-points in OOXML
                entry["size_pt"] = int(sz.get(f"{W}val")) / 2
            color = rpr.find(f"{W}color")
            if color is not None and color.get(f"{W}val") and color.get(f"{W}val") != "auto":
                entry["color"] = "#" + color.get(f"{W}val").upper()
        styles.append(entry)
    return styles


def extract_brand(path: str, media_dir: str | None = None) -> dict:
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise SystemExit(f"error: not a readable .docx file ({path}): {exc}")
    with zf:
        theme = _extract_theme(zf)
        return {
            "source": os.path.basename(path),
            "palette": theme["palette"],
            "fonts": theme["fonts"],
            "heading_styles": _extract_heading_styles(zf),
            **_extract_header_footer(zf),
            "media": _extract_media(zf, media_dir),
        }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Extract a brand kit from a .docx file.")
    ap.add_argument("docx", help="path to the .docx file")
    ap.add_argument("-o", "--output", help="write JSON to this file instead of stdout")
    ap.add_argument("--media-dir", help="also save embedded media (logos) into this dir")
    args = ap.parse_args(argv)

    profile = extract_brand(args.docx, args.media_dir)
    payload = json.dumps(profile, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
        print(f"wrote brand profile to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(payload + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
