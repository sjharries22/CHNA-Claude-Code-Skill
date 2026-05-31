# From a previous report to a branded HTML report

A self-contained HTML file is the most controllable CHNA deliverable: the
brand maps directly to CSS, it opens in any browser with no dependencies, and
it prints to PDF. This is the recommended path when a client wants a new report
that matches a previous one's brand, structure, and tone.

## Why HTML (vs. Gamma)

- **Exact brand control** — colors and fonts become CSS custom properties, so
  the output matches the source palette/typeface precisely.
- **Portable** — one file; CSS and the logo (as a data URI) are inlined.
- **PDF-ready** — a print stylesheet is included; WeasyPrint or a browser's
  "Print to PDF" produces a clean PDF.
- **Versionable** — plain text, so it diffs and lives in git.

Use Gamma instead when the client specifically wants an editable slide deck
(see `gamma_pipeline.md`).

## Step 1 — Extract the brand

- **PDF source:** `python3 scripts/extract_brand_pdf.py "PREV.pdf" -o profile.json --image-dir out/img`
  (needs `pip install pymupdf`). Gives dominant fonts, text + fill colors, the
  embedded logo image, and heading candidates.
- **.docx source:** `python3 scripts/extract_brand.py "PREV.docx" -o profile.json --media-dir out/img`

Normalize the findings into a **`brand.json`**:

```json
{
  "org": "AdventHealth Ottawa",
  "tagline": "Extending the Healing Ministry of Christ",
  "colors": {"primary": "#005C95", "primary_dark": "#005080", "accent": "#1DA8E1",
             "text": "#545E66", "muted": "#79858C", "band": "#005C95"},
  "fonts": {"heading": "'proxima-nova', Montserrat, Arial, sans-serif",
            "body": "'proxima-nova', 'Open Sans', Arial, sans-serif"},
  "logo": "out/img/logo.png"
}
```

Tips: `colors.primary` is usually the heading color; `accent` is a brighter
secondary; `text`/`muted` are the two body grays; `band` is the cover banner.
Brand fonts are often licensed (e.g. Proxima Nova) — list the brand font first
and a close web-safe fallback (Montserrat/Open Sans) after it.

## Step 2 — Draft content in the previous report's structure & tone

Read the previous report's text (e.g. via `read_file_content` on the source, or
`extract_docx.py`). Mirror its section order and voice, then write a
**`content.json`**:

```json
{
  "title": "2023 Community Health Needs Assessment",
  "subtitle": "AdventHealth Ottawa",
  "cover_note": "Approved by the Hospital Board on ...",
  "hero_image": "out/img/cover.png",
  "sections": [
    {"number": "1", "title": "Executive Summary", "blocks": [
      {"type": "h3", "text": "Goals"},
      {"type": "p", "text": "..."},
      {"type": "ul", "items": ["...", "..."]},
      {"type": "table", "headers": ["Indicator", "County", "State"],
                        "rows": [["Adult obesity", "34%", "30%"]]},
      {"type": "callout", "text": "Key takeaway ..."}
    ]}
  ]
}
```

Block types: `h3`, `p`, `ul`, `ol`, `table`, `callout`, `image`. **Never invent
figures, quotes, or dates** — pull them from inputs and leave a `{{TODO}}`
marker if missing.

## Step 3 — Render

```bash
python3 scripts/build_html_report.py --brand brand.json --content content.json -o report.html
```

The output inlines the CSS and embeds images as data URIs, so it is fully
self-contained.

## Step 4 — Preview / export to PDF (optional)

```bash
pip install weasyprint
python3 -c "from weasyprint import HTML; HTML('report.html').write_pdf('report.pdf')"
```

To preview as an image, render the PDF with PyMuPDF:
`python3 -c "import fitz; fitz.open('report.pdf')[0].get_pixmap().save('preview.png')"`.

## Guardrails

- The brand is the source of visual truth; reproduce it, don't reinvent it.
- Don't fabricate data; treat resident quotes/stories as sensitive — paraphrase.
- Keep the brand font first in the stack but always provide a free fallback,
  since licensed fonts won't be present on every viewer's machine.
