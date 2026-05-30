# Example: AdventHealth Ottawa (2020 CHNA)

A worked `brand.json` + `content.json` pair, derived from the published
AdventHealth Ottawa 2020 Community Health Needs Assessment, showing how the
HTML pipeline reproduces a client's brand.

The brand (`#005C95` blue, Proxima Nova, gray body text) and the Executive
Summary content were extracted with `scripts/extract_brand_pdf.py` and read
from the source PDF.

## Run it

```bash
python3 ../../scripts/build_html_report.py \
  --brand brand.json --content content.json -o report.html
```

Open `report.html` in a browser, or export a PDF:

```bash
pip install weasyprint
python3 -c "from weasyprint import HTML; HTML('report.html').write_pdf('report.pdf')"
```

## Assets are intentionally not committed

`brand.json` references `logo.png` and `content.json` references `cover.png`,
which are **not** included here — the AdventHealth logo and photography are
the client's property. Drop those files into this folder to render the full
branded cover; without them the generator falls back to a wordmark and a
gradient banner, so the example still runs.
