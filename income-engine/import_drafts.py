"""Import hand-written emails (e.g. drafted with Claude in chat, no API cost) into data/drafts.csv.

data/drafts_written.jsonl: one JSON object per line: {"name", "subject", "body"}
The body may contain {signature}; send_emails.py fills in your name, postal
address and opt-out line. Everything imports as status=draft.

    python import_drafts.py
"""
import json

import config
from csvio import read_rows, write_rows

SRC = config.DATA / "drafts_written.jsonl"


def main():
    audited = {r["name"]: r for r in read_rows(config.AUDITED_CSV)}
    drafts = {d["place_id"]: d for d in read_rows(config.DRAFTS_CSV)}
    added = 0
    for line in SRC.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        w = json.loads(line)
        lead = audited.get(w["name"])
        if not lead or not lead.get("email"):
            print(f"skip {w['name']}: not in audited.csv or no email")
            continue
        if lead["place_id"] in drafts and drafts[lead["place_id"]]["status"] != "draft":
            continue  # already approved/sent; don't overwrite
        drafts[lead["place_id"]] = {"place_id": lead["place_id"], "name": w["name"], "email": lead["email"],
                                    "subject": w["subject"], "body": w["body"], "status": "draft"}
        added += 1
    write_rows(config.DRAFTS_CSV, list(drafts.values()))
    print(f"{added} drafts imported -> {config.DRAFTS_CSV} (status=draft; nothing sends until approved)")


if __name__ == "__main__":
    main()
