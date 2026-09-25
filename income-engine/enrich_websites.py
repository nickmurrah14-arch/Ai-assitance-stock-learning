"""Find websites for Florida license leads for free by trying likely domains.

"Deltona Heat And Air INC" -> deltonaheatandair.com, deltonaheatair.com, deltonaheatandairfl.com, ...
A candidate only counts if the page mentions a distinctive word from the business
name, a trade word (air/plumb/hvac/...), and a local signal (Florida, a local area
code, or the city). Parked/for-sale domains are rejected.

    python enrich_websites.py --limit 200          # first 200 rows of data/fl_licensees.csv
    python enrich_websites.py --limit 200 --export # also copy them into data/leads.csv for audit_sites.py
"""
import argparse
import re
from concurrent.futures import ThreadPoolExecutor

import requests

import config
from csvio import read_rows, write_rows

SRC = config.DATA / "fl_licensees.csv"
UA = "Mozilla/5.0 (compatible; site-audit/1.0)"
SUFFIXES = {"llc", "inc", "corp", "corporation", "co", "company", "pa", "the", "lc", "l", "c", "ltd"}
GENERIC = {"air", "heating", "cooling", "heat", "cool", "conditioning", "plumbing", "plumber", "mechanical",
           "services", "service", "systems", "and", "of", "florida", "central", "hvac", "ac", "a",
           "contractors", "contracting", "solutions", "repair", "home", "comfort", "pro", "pros"}
TRADE_RE = re.compile(r"plumb|air condition|\bhvac\b|\ba/?c\b|cooling|heating|heat pump|water heater|drain", re.I)
LOCAL_RE = re.compile(r"florida|\bfl\b|\(?386\)?|\(?407\)?|\(?321\)?|\(?689\)?", re.I)
PARKED_RE = re.compile(r"domain (is )?for sale|buy this domain|parked free|this domain may be for sale|godaddy\.com/domainsearch", re.I)


def words(name: str) -> list[str]:
    w = re.sub(r"[^a-z0-9& ]", " ", name.lower().replace("'", "")).replace("&", " and ").split()
    while w and w[-1] in SUFFIXES:
        w.pop()
    return w


def candidates(name: str) -> list[str]:
    w = words(name)
    if not w:
        return []
    joined = "".join(w)
    no_and = "".join(x for x in w if x != "and")
    bases = list(dict.fromkeys([joined, no_and]))
    out = []
    for b in bases:
        out += [f"{b}.com", f"{b}fl.com", f"{b}.net"]
    out += [f"{bases[0]}florida.com", f"{bases[0]}inc.com", f"{bases[0]}llc.com"]
    return [d for d in dict.fromkeys(out) if 4 < len(d) < 64]


def matches(html: str, name: str, city: str) -> bool:
    text = re.sub(r"<[^>]+>", " ", html)
    if PARKED_RE.search(text):
        return False
    distinctive = [x for x in words(name) if x not in GENERIC and len(x) > 2]
    if distinctive and not any(re.search(rf"\b{re.escape(x)}\b", text, re.I) for x in distinctive):
        return False
    local = LOCAL_RE.search(text) or (city and city.lower() in text.lower())
    return bool(TRADE_RE.search(text) and local)


def find_site(row: dict) -> str:
    for domain in candidates(row["name"]):
        for url in (f"https://{domain}", f"https://www.{domain}", f"http://{domain}"):
            try:
                r = requests.get(url, headers={"User-Agent": UA}, timeout=8, allow_redirects=True)
            except requests.RequestException:
                continue
            if r.ok and matches(r.text, row["name"], row.get("city", "")):
                return r.url
            break  # domain answered but didn't match; try the next domain
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100, help="how many rows (top of the list) to try")
    ap.add_argument("--export", action="store_true", help="copy the processed rows into data/leads.csv")
    args = ap.parse_args()
    rows = read_rows(SRC)
    if not rows:
        raise SystemExit("Run florida_leads.py first")
    todo = [r for r in rows[: args.limit] if not r.get("website") and r.get("website_source") != "guess-none"]
    print(f"Trying domains for {len(todo)} businesses...")
    with ThreadPoolExecutor(max_workers=12) as pool:
        for row, site in zip(todo, pool.map(find_site, todo)):
            row["website"] = site
            row["website_source"] = "guess" if site else "guess-none"
            print(f"  {row['name']}: {site or '-'}")
    write_rows(SRC, rows)
    found = sum(1 for r in rows[: args.limit] if r.get("website"))
    print(f"{found}/{min(args.limit, len(rows))} have a website -> {SRC}")
    if args.export:
        leads = {r["place_id"]: r for r in read_rows(config.LEADS_CSV)}
        for r in rows[: args.limit]:
            leads[r["place_id"]] = {**leads.get(r["place_id"], {}), **r}
        write_rows(config.LEADS_CSV, list(leads.values()))
        print(f"Exported to {config.LEADS_CSV}; next: python audit_sites.py")


if __name__ == "__main__":
    main()
