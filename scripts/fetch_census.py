#!/usr/bin/env python3
"""Fetch American Community Survey (ACS) data from the Census Bureau API.

Pulls the demographic / social-determinant variables that populate a CHNA's
"Community Description" and data sections, for a given county (or state).

Requires a free Census API key (https://api.census.gov/data/key_signup.html),
read from the ``CENSUS_API_KEY`` environment variable -- the key is never
written to disk by this script.

Usage:
    export CENSUS_API_KEY=...                 # your key
    # Franklin County, KS (state 20, county 059), default variable set:
    python3 fetch_census.py --state 20 --county 059 -o census.json
    # custom variables / dataset year:
    python3 fetch_census.py --state 20 --county 059 \
        --vars B01003_001E,B19013_001E --year 2022 -o census.json

Output is a JSON object mapping each variable to its value (plus NAME), with a
small set of derived percentages when the inputs are present.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

# A sensible default ACS 5-year variable set for a CHNA community profile.
DEFAULT_VARS = {
    "B01003_001E": "total_population",
    "B01002_001E": "median_age",
    "B19013_001E": "median_household_income",
    "B19301_001E": "per_capita_income",
    "B17001_001E": "poverty_universe",
    "B17001_002E": "poverty_below",
    "B02001_002E": "race_white",
    "B02001_003E": "race_black",
    "B02001_005E": "race_asian",
    "B03003_003E": "hispanic_or_latino",
    "B11001_001E": "households",
    "B25077_001E": "median_home_value",
    "B25064_001E": "median_gross_rent",
}


def fetch(state: str, county: str | None, variables: list[str], year: int,
          dataset: str, key: str) -> dict[str, str]:
    base = f"https://api.census.gov/data/{year}/{dataset}"
    params = {
        "get": "NAME," + ",".join(variables),
        "for": f"county:{county}" if county else f"state:{state}",
        "key": key,
    }
    if county:
        params["in"] = f"state:{state}"
    url = f"{base}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    header, row = data[0], data[1]
    return dict(zip(header, row))


def add_derived(out: dict) -> dict:
    def num(code):
        try:
            return float(out["raw"][code])
        except (KeyError, ValueError, TypeError):
            return None

    pop = num("B01003_001E")
    derived: dict[str, float] = {}
    pov_u, pov_b = num("B17001_001E"), num("B17001_002E")
    if pov_u and pov_b is not None:
        derived["poverty_rate_pct"] = round(100 * pov_b / pov_u, 1)
    if pop:
        for code, label in (("B02001_002E", "pct_white"), ("B02001_003E", "pct_black"),
                            ("B02001_005E", "pct_asian"), ("B03003_003E", "pct_hispanic")):
            v = num(code)
            if v is not None:
                derived[label] = round(100 * v / pop, 1)
    out["derived"] = derived
    return out


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Fetch ACS data for a CHNA community profile.")
    ap.add_argument("--state", required=True, help="state FIPS, e.g. 20 (Kansas)")
    ap.add_argument("--county", help="county FIPS, e.g. 059 (Franklin)")
    ap.add_argument("--vars", help="comma-separated variable codes (default: CHNA set)")
    ap.add_argument("--year", type=int, default=2022, help="ACS year (default 2022)")
    ap.add_argument("--dataset", default="acs/acs5", help="dataset path (default acs/acs5)")
    ap.add_argument("-o", "--output", help="write JSON here instead of stdout")
    args = ap.parse_args(argv)

    key = os.environ.get("CENSUS_API_KEY")
    if not key:
        raise SystemExit("error: set CENSUS_API_KEY (https://api.census.gov/data/key_signup.html)")

    variables = args.vars.split(",") if args.vars else list(DEFAULT_VARS)
    try:
        raw = fetch(args.state, args.county, variables, args.year, args.dataset, key)
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"error: Census API request failed: {exc}")

    labels = DEFAULT_VARS if not args.vars else {}
    out = {
        "name": raw.get("NAME", ""),
        "year": args.year,
        "dataset": args.dataset,
        "labels": {k: v for k, v in labels.items() if k in raw},
        "raw": {k: v for k, v in raw.items() if k not in ("NAME", "state", "county")},
    }
    out = add_derived(out)

    payload = json.dumps(out, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(payload + "\n")
        print(f"wrote ACS data for {out['name']} to {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(payload + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
