"""Merge hand research into the lead files, matched by business name.

data/manual_research.csv columns: name, phone, website, notes, skip
- phone / website / notes overwrite what the scripts found (blank cells are ignored)
- skip: any text (e.g. "big company", "out of area") drops the business from
  leads.csv and audited.csv
If a researched website differs from the audited one, the row is dropped from
audited.csv so the next `python audit_sites.py` re-audits the right site.

    python apply_research.py
"""
import config
from csvio import read_rows, write_rows

RESEARCH = config.DATA / "manual_research.csv"


def main():
    research: dict[str, dict] = {}
    for r in read_rows(RESEARCH):  # later rows win, so you can append corrections
        research[r["name"]] = {**research.get(r["name"], {}), **{k: v for k, v in r.items() if v}}
    for path in (config.DATA / "fl_licensees.csv", config.LEADS_CSV, config.AUDITED_CSV):
        rows, keep = read_rows(path), []
        for row in rows:
            m = research.get(row["name"], {})
            if m.get("skip"):
                row["skip"] = m["skip"]
                if path != config.DATA / "fl_licensees.csv":
                    continue
            if m:
                if path == config.AUDITED_CSV and m.get("website") and m["website"] != row.get("website"):
                    continue
                for k in ("phone", "website", "notes"):
                    if m.get(k):
                        row[k] = m[k]
                row["researched"] = "yes"
            keep.append(row)
        write_rows(path, keep)
        print(f"{path.name}: {len(keep)} rows, {sum(1 for r in keep if r.get('researched'))} researched")


if __name__ == "__main__":
    main()
