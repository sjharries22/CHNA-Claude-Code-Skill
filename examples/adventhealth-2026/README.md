# Example: AdventHealth Ottawa — new cycle (2026 CHNA draft)

A worked example of the full pipeline: take a previous report's brand +
structure + tone and produce a **new-cycle** report populated with fresh
**U.S. Census Bureau** data.

- `brand.json` — AdventHealth brand (extracted from the 2020 PDF with
  `scripts/extract_brand_pdf.py`).
- `census.json` — Franklin County, KS ACS 2018–2022 5-year data, pulled with
  `scripts/fetch_census.py` (state 20, county 059).
- `content.json` — a 2026 CHNA draft following the 2020 section structure and
  tone, with the Census figures filled into the demographics and data tables.

## Reproduce the data pull

```bash
export CENSUS_API_KEY=...     # free: https://api.census.gov/data/key_signup.html
python3 ../../scripts/fetch_census.py --state 20 --county 059 -o census.json
```

## Render

```bash
python3 ../../scripts/build_html_report.py \
  --brand brand.json --content content.json -o report.html
```

## Notes

- `brand.json` references `logo.png` and `content.json` references `cover.png`,
  which are **not** committed (AdventHealth's logo and photography are the
  client's property). Add them to this folder to render the full branded cover;
  without them the generator falls back to a wordmark and gradient banner.
- `{{...}}` markers in `content.json` flag content the Hospital must confirm
  (final priorities, adoption date) — the pipeline never fabricates
  hospital-specific facts; only the Census figures are real and sourced.
