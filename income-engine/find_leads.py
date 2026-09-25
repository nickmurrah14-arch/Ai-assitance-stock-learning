"""Step 1: find local businesses with the Google Places API (New) Text Search.

Free tier (2026): 5,000 Text Search Pro calls/month, 20 results per call.

    python find_leads.py "plumbers in Austin, TX" "roofers in Austin, TX" --pages 3
"""
import argparse
import time

import requests

import config
from csvio import read_rows, write_rows

URL = "https://places.googleapis.com/v1/places:searchText"
FIELDS = ",".join(
    [
        "places.id",
        "places.displayName",
        "places.formattedAddress",
        "places.nationalPhoneNumber",
        "places.websiteUri",
        "places.rating",
        "places.userRatingCount",
        "places.businessStatus",
        "places.primaryType",
        "nextPageToken",
    ]
)


def search(query: str, pages: int) -> list[dict]:
    headers = {
        "X-Goog-Api-Key": config.GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": FIELDS,
    }
    body: dict = {"textQuery": query, "pageSize": 20}
    out = []
    for _ in range(pages):
        r = requests.post(URL, json=body, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        for p in data.get("places", []):
            if p.get("businessStatus", "OPERATIONAL") != "OPERATIONAL":
                continue
            out.append(
                {
                    "place_id": p["id"],
                    "name": p.get("displayName", {}).get("text", ""),
                    "category": p.get("primaryType", ""),
                    "address": p.get("formattedAddress", ""),
                    "phone": p.get("nationalPhoneNumber", ""),
                    "website": p.get("websiteUri", ""),
                    "rating": p.get("rating", ""),
                    "reviews": p.get("userRatingCount", 0),
                    "query": query,
                }
            )
        token = data.get("nextPageToken")
        if not token:
            break
        body = {"textQuery": query, "pageSize": 20, "pageToken": token}
        time.sleep(2)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+", help='e.g. "HVAC companies in Denver, CO"')
    ap.add_argument("--pages", type=int, default=3, help="up to 3 pages of 20 per query")
    args = ap.parse_args()
    if not config.GOOGLE_PLACES_API_KEY:
        raise SystemExit("Set GOOGLE_PLACES_API_KEY in income-engine/.env")

    existing = {r["place_id"]: r for r in read_rows(config.LEADS_CSV)}
    added = 0
    for q in args.queries:
        for lead in search(q, args.pages):
            if lead["place_id"] not in existing:
                existing[lead["place_id"]] = lead
                added += 1
    write_rows(config.LEADS_CSV, list(existing.values()))
    print(f"{added} new leads, {len(existing)} total -> {config.LEADS_CSV}")


if __name__ == "__main__":
    main()
