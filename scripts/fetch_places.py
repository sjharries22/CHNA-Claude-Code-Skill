#!/usr/bin/env python3
"""Fetch county health-indicator prevalence from the CDC PLACES dataset.

CDC PLACES (https://data.cdc.gov) provides model-based estimates of chronic
disease, behavioral, prevention, and social-determinant measures down to the
county level — the clinical complement to the Census/ACS demographics that
``fetch_census.py`` returns.

Data comes from the Socrata API. An app token is optional but avoids
throttling; if set, it is read from ``SOCRATA_APP_TOKEN`` (never stored here).

Usage:
    # Franklin County, KS = FIPS 20059
    python3 fetch_places.py --fips 20059 -o places.json
    # only specific measures, crude (not age-adjusted) prevalence:
    python3 fetch_places.py --fips 20059 --measures OBESITY,DIABETES,DEPRESSION \
        --value-type "Crude prevalence" -o places.json

Output maps each MeasureId to its prevalence value (percent) and release year.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

# County-level PLACES dataset (current release).
DATASET = "swc5-untb"
BASE = f"https://data.cdc.gov/resource/{DATASET}.json"

# A useful default CHNA measure set (MeasureId -> friendly label).
DEFAULT_MEASURES = {
    "OBESITY": "Adult obesity",
    "DIABETES": "Diagnosed diabetes",
    "BPHIGH": "High blood pressure",
    "HIGHCHOL": "High cholesterol",
    "CHD": "Coronary heart disease",
    "STROKE": "Stroke",
    "CANCER": "Cancer (excl. skin)",
    "COPD": "COPD",
    "CASTHMA": "Current asthma",
    "CSMOKING": "Current smoking",
    "BINGE": "Binge drinking",
    "LPA": "No leisure-time physical activity",
    "DEPRESSION": "Depression",
    "MHLTH": "Frequent mental distress",
    "ACCESS2": "Uninsured (age 18–64)",
    "CHECKUP": "Routine checkup (past year)",
    "FOODINSECU": "Food insecurity",
    "HOUSINSECU": "Housing insecurity",
    "LACKTRPT": "Lack of reliable transportation",
}


def fetch(fips: str, value_type: str, token: str | None) -> list[dict]:
    params = {
        "locationid": fips,
        "data_value_type": value_type,
        "$select": "measureid,measure,data_value,year,category",
        "$limit": "500",
    }
    url = f"{BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    if token:
        req.add_header("X-App-Token", token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Fetch CDC PLACES county health indicators.")
    ap.add_argument("--fips", required=True, help="5-digit county FIPS, e.g. 20059")
    ap.add_argument("--measures", help="comma-separated MeasureIds (default: CHNA set)")
    ap.add_argument("--value-type", default="Age-adjusted prevalence",
                    help="'Age-adjusted prevalence' (default) or 'Crude prevalence'")
    ap.add_argument("-o", "--output", help="write JSON here instead of stdout")
    args = ap.parse_args(argv)

    token = os.environ.get("SOCRATA_APP_TOKEN")
    try:
        rows = fetch(args.fips, args.value_type, token)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"error: CDC PLACES request failed: {exc}")

    wanted = set(args.measures.split(",")) if args.measures else set(DEFAULT_MEASURES)
    indicators: dict[str, dict] = {}
    for r in rows:
        mid = r.get("measureid")
        if mid in wanted and mid not in indicators:
            indicators[mid] = {
                "label": DEFAULT_MEASURES.get(mid, r.get("measure", mid)),
                "value_pct": float(r["data_value"]) if r.get("data_value") else None,
                "year": r.get("year"),
                "category": r.get("category"),
            }

    out = {
        "fips": args.fips,
        "value_type": args.value_type,
        "indicators": indicators,
    }
    payload = json.dumps(out, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
        print(f"wrote {len(indicators)} indicators for FIPS {args.fips} to {args.output}",
              file=sys.stderr)
    else:
        sys.stdout.write(payload + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
