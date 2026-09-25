"""Build data/call_sheet.csv: every audited business with a phone number, best first.

Priority 1: no website found and hand-researched (strongest "you rely on the phone" angle)
Priority 2: has a website with gaps, no email draft
Priority 3: also has an email draft (call a few days after the email)
Skips rows flagged by audit_sites.py as possibly another company's site.
Re-running keeps everything you logged (result, notes, follow-up date, call history).

    python make_call_sheet.py
"""
import config
from csvio import read_rows, write_rows
from florida_leads import CITY_ORDER

OUT = config.DATA / "call_sheet.csv"
KEEP = ("result", "follow_up_date", "notes_from_calls", "last_called", "attempts")


def main():
    drafted = {d["name"] for d in read_rows(config.DRAFTS_CSV)}
    previous = {r.get("place_id") or r["name"]: r for r in read_rows(OUT)}
    sheet = []
    for r in read_rows(config.AUDITED_CSV):
        if not r.get("phone") or r.get("skip") or r.get("site_check"):
            continue
        no_site = not r.get("website")
        opener = ("I couldn't find a website for you, so I'm guessing most of your work comes by phone. "
                  if no_site else "")
        prev = previous.get(r.get("place_id")) or previous.get(r["name"]) or {}
        sheet.append({
            "place_id": r.get("place_id", ""),
            "priority": 1 if (no_site and r.get("researched")) else 3 if r["name"] in drafted else 2,
            "name": r["name"], "city": r.get("city", ""), "phone": r["phone"], "website": r.get("website", ""),
            "email_draft_ready": "yes" if r["name"] in drafted else "",
            "what_we_noticed": "; ".join(x for x in (r.get("issues", ""), r.get("notes", "")) if x),
            "opener": opener + "Do you ever miss calls while you're out on jobs? What happens to those?",
            **{k: prev.get(k, "") for k in KEEP},
        })

    def city_rank(city: str) -> int:
        return CITY_ORDER.index(city.upper()) if city.upper() in CITY_ORDER else len(CITY_ORDER)

    sheet.sort(key=lambda s: (s["priority"], city_rank(s["city"]), s["name"]))
    write_rows(OUT, sheet)
    print(f"{len(sheet)} businesses -> {OUT}")


if __name__ == "__main__":
    main()
