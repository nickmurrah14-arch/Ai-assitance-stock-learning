"""Free Florida lead source: every licensed AC, mechanical and plumbing contractor.

Uses the Florida DBPR public licensee file (public record, no key, no card):
https://www2.myfloridalicense.com/construction-industry/public-records/

It has business names and mailing addresses, but no phone, website or email.
Enrich the top rows (website, phone) before running audit_sites.py.

    python florida_leads.py                       # Volusia + Seminole, Deltona-first ordering
    python florida_leads.py --counties 74 69 48   # add Orange County
"""
import argparse
import csv
from pathlib import Path

import requests

import config
from csvio import read_rows, write_rows

URL = "https://www2.myfloridalicense.com/sto/file_download/extracts//CONSTRUCTIONLICENSE_1.csv"
CACHE = config.DATA / "fl_construction_licenses.csv"

# DBPR county codes = 10 + alphabetical position (Dade counted as "Dade").
COUNTIES = {"74": "Volusia", "69": "Seminole", "48": "Orange", "28": "Flagler", "35": "Lake", "15": "Brevard"}
TRADES = {"CAC": "AC", "RA": "AC", "CMC": "mechanical/HVAC", "RM": "mechanical/HVAC", "CFC": "plumbing", "RF": "plumbing"}
# Closest to Deltona first; anything else in the chosen counties comes after.
CITY_ORDER = [
    "DELTONA", "DEBARY", "ORANGE CITY", "DELAND", "DE LAND", "LAKE HELEN", "OSTEEN", "ENTERPRISE",
    "SANFORD", "LAKE MARY", "LONGWOOD", "WINTER SPRINGS", "OVIEDO", "CASSELBERRY", "ALTAMONTE SPRINGS",
    "GENEVA", "DAYTONA BEACH", "PORT ORANGE", "ORMOND BEACH", "HOLLY HILL", "SOUTH DAYTONA",
    "NEW SMYRNA BEACH", "EDGEWATER",
]

# Column positions in the DBPR licensee extract (no header row).
OCC, NAME, DBA, ADDR1, ADDR2, CITY, ZIP, COUNTY, STATUS, ORIG_DATE, LICENSE = 1, 2, 3, 5, 6, 8, 10, 11, 14, 15, 20


def download(force: bool = False) -> Path:
    if force or not CACHE.exists():
        print("Downloading DBPR licensee file (~45 MB)...")
        with requests.get(URL, stream=True, timeout=300) as r:
            r.raise_for_status()
            with CACHE.open("wb") as f:
                for chunk in r.iter_content(1 << 20):
                    f.write(chunk)
    return CACHE


UPPER_WORDS = {"LLC", "INC", "LLP", "PA", "USA", "HVAC", "AC", "A/C", "II", "III", "LP", "CO", "DBA"}


def nice_name(name: str) -> str:
    """'JIM'S PLUMBING, LLC' -> "Jim's Plumbing, LLC" (DBPR stores everything uppercase)."""
    if not name.isupper():
        return name
    out = []
    for w in name.split():
        core = w.strip(",.").upper()
        out.append(w.upper() if core in UPPER_WORDS else w[:1].upper() + w[1:].lower())
    return " ".join(out)


def city_rank(city: str) -> int:
    return CITY_ORDER.index(city) if city in CITY_ORDER else len(CITY_ORDER)


def business_rows(path: Path, counties: set[str]) -> list[dict]:
    """One row per business, active licenses only, closest cities first."""
    by_business: dict[str, dict] = {}
    with path.open(encoding="latin-1", newline="") as f:
        for r in csv.reader(f):
            if len(r) <= LICENSE or r[OCC] not in TRADES or r[COUNTY] not in counties or r[STATUS] != "A":
                continue
            dba = r[DBA].strip()
            if dba.upper() in ("INDIVIDUAL", "SELF", "NONE"):
                dba = ""
            name = dba or r[NAME].strip()
            key = name.upper().replace(",", "").replace(".", "")
            trade = TRADES[r[OCC]]
            if key in by_business:
                if trade not in by_business[key]["trade"]:
                    by_business[key]["trade"] += f" + {trade}"
                continue
            city = r[CITY].strip().upper()
            by_business[key] = {
                "place_id": r[LICENSE],
                "name": nice_name(name),
                "licensee": r[NAME].strip(),
                "trade": trade,
                "category": trade,
                "address": ", ".join(p for p in (r[ADDR1].strip(), r[ADDR2].strip(), city.title(), "FL", r[ZIP].strip()) if p),
                "city": city.title(),
                "county": COUNTIES.get(r[COUNTY], r[COUNTY]),
                "licensed_since": r[ORIG_DATE],
                "is_business_name": "yes" if dba else "no",
                "phone": "",
                "website": "",
                "reviews": "",
                "source": "dbpr",
            }
    rows = list(by_business.values())
    # Named businesses before sole proprietors, then nearest city.
    rows.sort(key=lambda b: (b["is_business_name"] != "yes", city_rank(b["city"].upper()), b["name"]))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--counties", nargs="+", default=["74", "69"], help="DBPR county codes (74 Volusia, 69 Seminole)")
    ap.add_argument("--refresh", action="store_true", help="re-download the DBPR file")
    args = ap.parse_args()
    rows = business_rows(download(args.refresh), set(args.counties))
    out = config.DATA / "fl_licensees.csv"
    # Keep enrichment (phone/website) already added by hand or by research.
    old = {r["place_id"]: r for r in read_rows(out)}
    for r in rows:
        for k in ("phone", "website", "email", "notes"):
            if old.get(r["place_id"], {}).get(k):
                r[k] = old[r["place_id"]][k]
    write_rows(out, rows)
    named = sum(1 for r in rows if r["is_business_name"] == "yes")
    print(f"{len(rows)} active AC/mechanical/plumbing businesses ({named} with a business name) -> {out}")


if __name__ == "__main__":
    main()
