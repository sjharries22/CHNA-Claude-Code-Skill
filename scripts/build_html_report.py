#!/usr/bin/env python3
"""Render a CHNA report as a self-contained, brand-styled HTML file.

Inputs are two JSON files so the generator stays client-agnostic:

  * a **brand** file (palette, fonts, org, tagline, optional logo) -- usually
    derived from ``extract_brand_pdf.py`` / ``extract_brand.py`` output
  * a **content** file (title + ordered sections of typed blocks)

The brand drives CSS custom properties, so the same content renders in any
client's colors/fonts. The output is one HTML file with the CSS inlined and
the logo embedded as a data URI, so it is fully portable and prints cleanly to
PDF (print stylesheet included).

Usage:
    python3 build_html_report.py --brand brand.json --content content.json -o report.html

Content schema (JSON):
    {
      "title": "2023 Community Health Needs Assessment",
      "subtitle": "AdventHealth Ottawa",
      "cover_note": "Approved by the Hospital Board on ...",
      "hero_image": "out/img/cover.png",          # optional
      "sections": [
        {"number": "1", "title": "Executive Summary", "blocks": [
           {"type": "h3", "text": "Goals"},
           {"type": "p",  "text": "..."},
           {"type": "ul", "items": ["...", "..."]},
           {"type": "table", "headers": ["Indicator","County","State"],
                              "rows": [["Adult obesity","34%","30%"]]},
           {"type": "callout", "text": "Key takeaway ..."}
        ]}
      ]
    }

Brand schema (JSON):
    {
      "org": "AdventHealth Ottawa",
      "tagline": "Extending the Healing Ministry of Christ",
      "colors": {"primary":"#005C95","primary_dark":"#005080","accent":"#1DA8E1",
                 "text":"#545E66","muted":"#79858C","band":"#005C95"},
      "fonts": {"heading":"'proxima-nova', Montserrat, Arial, sans-serif",
                "body":"'proxima-nova', 'Open Sans', Arial, sans-serif"},
      "logo": "out/img/logo.png"                  # optional
    }
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import os
import sys

DEFAULT_COLORS = {
    "primary": "#005C95", "primary_dark": "#005080", "accent": "#1DA8E1",
    "text": "#545E66", "muted": "#79858C", "band": "#005C95",
}
DEFAULT_FONTS = {
    "heading": "'proxima-nova', Montserrat, 'Segoe UI', Arial, sans-serif",
    "body": "'proxima-nova', 'Open Sans', 'Segoe UI', Arial, sans-serif",
}


def _data_uri(path: str | None) -> str | None:
    if not path or not os.path.exists(path):
        return None
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _esc(text: str) -> str:
    return html.escape(str(text), quote=False)


def render_block(block: dict) -> str:
    t = block.get("type")
    if t == "h3":
        return f"<h3>{_esc(block['text'])}</h3>"
    if t == "p":
        return f"<p>{_esc(block['text'])}</p>"
    if t == "ul":
        items = "".join(f"<li>{_esc(i)}</li>" for i in block.get("items", []))
        return f"<ul>{items}</ul>"
    if t == "ol":
        items = "".join(f"<li>{_esc(i)}</li>" for i in block.get("items", []))
        return f"<ol>{items}</ol>"
    if t == "callout":
        return f"<div class='callout'>{_esc(block['text'])}</div>"
    if t == "table":
        head = "".join(f"<th>{_esc(h)}</th>" for h in block.get("headers", []))
        body = "".join(
            "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in row) + "</tr>"
            for row in block.get("rows", [])
        )
        thead = f"<thead><tr>{head}</tr></thead>" if head else ""
        return f"<table>{thead}<tbody>{body}</tbody></table>"
    if t == "image":
        uri = _data_uri(block.get("src")) or block.get("src", "")
        cap = f"<figcaption>{_esc(block['caption'])}</figcaption>" if block.get("caption") else ""
        return f"<figure><img src='{uri}' alt=''/>{cap}</figure>"
    return ""


def render_section(section: dict) -> str:
    num = section.get("number")
    label = f"{num}. {section['title']}" if num else section["title"]
    blocks = "".join(render_block(b) for b in section.get("blocks", []))
    return (
        "<section class='report-section'>"
        f"<h2>{_esc(label)}</h2>{blocks}</section>"
    )


def build_css(colors: dict, fonts: dict) -> str:
    c = {**DEFAULT_COLORS, **colors}
    f = {**DEFAULT_FONTS, **fonts}
    return f"""
:root {{
  --primary:{c['primary']}; --primary-dark:{c['primary_dark']}; --accent:{c['accent']};
  --text:{c['text']}; --muted:{c['muted']}; --band:{c['band']};
  --heading-font:{f['heading']}; --body-font:{f['body']};
}}
* {{ box-sizing:border-box; }}
body {{ margin:0; color:var(--text); font-family:var(--body-font);
        font-size:15px; line-height:1.6; background:#fff; }}
.page {{ max-width:850px; margin:0 auto; padding:0 56px; }}

/* Cover */
.cover {{ padding:0; }}
.cover .cover-head {{ padding:56px 56px 24px; }}
.cover .org {{ font-family:var(--heading-font); font-weight:700; color:var(--primary);
               font-size:26px; letter-spacing:.2px; }}
.cover .title {{ font-family:var(--heading-font); font-weight:300; color:var(--primary);
                 font-size:34px; line-height:1.15; text-transform:uppercase; margin-top:6px; }}
.cover .hero {{ width:100%; display:block; }}
.cover .hero-fallback {{ width:100%; height:300px; background:linear-gradient(135deg,var(--primary),var(--accent)); }}
.cover .band {{ background:var(--band); color:#fff; padding:32px 56px;
                display:flex; justify-content:space-between; align-items:flex-end; gap:24px; }}
.cover .band .meta {{ font-size:13px; line-height:1.7; }}
.cover .band .tagline {{ font-style:italic; margin-top:14px; opacity:.95; }}
.cover .logo {{ background:#fff; border-radius:10px; padding:14px 18px; max-width:230px; }}
.cover .logo img {{ max-width:200px; display:block; }}
.cover .logo .wordmark {{ font-family:var(--heading-font); font-weight:700;
                          color:var(--primary); font-size:22px; white-space:nowrap; }}

/* Sections */
.report-section {{ padding:40px 0 8px; border-top:1px solid #eef1f3; }}
.report-section:first-of-type {{ border-top:none; }}
h2 {{ font-family:var(--heading-font); font-weight:700; color:var(--primary);
      font-size:26px; text-transform:uppercase; letter-spacing:.3px; margin:0 0 18px; }}
h3 {{ font-family:var(--heading-font); font-weight:700; color:var(--primary);
      font-size:17px; margin:26px 0 8px; }}
p {{ margin:0 0 12px; }}
ul, ol {{ margin:0 0 14px; padding-left:22px; }}
li {{ margin:4px 0; }}
ul li::marker {{ color:var(--accent); }}
.callout {{ border-left:4px solid var(--accent); background:#f3f8fc;
            padding:14px 18px; margin:16px 0; color:var(--primary-dark); font-weight:600; }}
table {{ border-collapse:collapse; width:100%; margin:14px 0; font-size:14px; }}
th {{ background:var(--primary); color:#fff; text-align:left; padding:8px 12px;
      font-family:var(--heading-font); font-weight:600; }}
td {{ padding:8px 12px; border-bottom:1px solid #e6eaed; }}
tr:nth-child(even) td {{ background:#f7f9fb; }}
figure {{ margin:16px 0; }} figure img {{ max-width:100%; }}
figcaption {{ font-size:12px; color:var(--muted); margin-top:6px; }}

@media print {{
  .page {{ max-width:none; padding:0 40px; }}
  .report-section {{ page-break-inside:avoid; }}
  h2 {{ page-break-after:avoid; }}
  .cover {{ page-break-after:always; }}
  @page {{ margin:0; size:Letter; }}
}}
"""


def build_html(brand: dict, content: dict) -> str:
    colors = brand.get("colors", {})
    fonts = brand.get("fonts", {})
    org = brand.get("org") or content.get("subtitle") or ""
    tagline = brand.get("tagline", "")
    logo_uri = _data_uri(brand.get("logo"))
    hero_uri = _data_uri(content.get("hero_image"))

    logo_html = (
        f"<img src='{logo_uri}' alt='{_esc(org)} logo'/>"
        if logo_uri else f"<div class='wordmark'>{_esc(org)}</div>"
    )
    hero_html = (
        f"<img class='hero' src='{hero_uri}' alt=''/>"
        if hero_uri else "<div class='hero-fallback'></div>"
    )
    cover_note = content.get("cover_note", "")
    meta_html = f"<div class='tagline'>{_esc(tagline)}</div>" if tagline else ""

    sections = "".join(render_section(s) for s in content.get("sections", []))

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{_esc(content.get('title',''))}</title>
<style>{build_css(colors, fonts)}</style></head>
<body>
<div class="cover">
  <div class="cover-head">
    <div class="org">{_esc(org)}</div>
    <div class="title">{_esc(content.get('title',''))}</div>
  </div>
  {hero_html}
  <div class="band">
    <div class="meta">{_esc(cover_note)}{meta_html}</div>
    <div class="logo">{logo_html}</div>
  </div>
</div>
<div class="page">
  {sections}
</div>
</body></html>
"""


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Render a CHNA report as branded HTML.")
    ap.add_argument("--brand", required=True, help="brand JSON file")
    ap.add_argument("--content", required=True, help="content JSON file")
    ap.add_argument("-o", "--output", required=True, help="output .html path")
    args = ap.parse_args(argv)

    with open(args.brand, encoding="utf-8") as fh:
        brand = json.load(fh)
    with open(args.content, encoding="utf-8") as fh:
        content = json.load(fh)

    out = build_html(brand, content)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"wrote {args.output} ({len(out)} bytes)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
