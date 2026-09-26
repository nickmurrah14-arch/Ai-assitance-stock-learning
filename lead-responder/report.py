"""Results report for one client: every missed call it caught and every lead it sent.

This is what turns the free month into a paying client. Send it around day 25 of the trial,
then monthly after that.

    python report.py --business +15551234567                          # last 30 days
    python report.py --business +15551234567 --start 2026-10-01 --end 2026-10-31

Writes a printable HTML page (reports/<name>-<start>-to-<end>.html) and prints a short text
summary you can paste into a text message to the owner.
"""
import argparse
import html
import json
import os
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GUARANTEE_MIN_LEADS = 2   # "any month it sends you fewer than 2 leads, you don't pay for that month"
MONTHLY_PRICE = 197


def build(db_path: str | Path, business: str, biz: dict, start: float, end: float) -> dict:
    db = sqlite3.connect(str(db_path))
    db.row_factory = sqlite3.Row
    db.executescript("CREATE TABLE IF NOT EXISTS calls (id INTEGER PRIMARY KEY, business TEXT, "
                     "caller TEXT, texted INTEGER, ts REAL)")
    calls = db.execute("SELECT caller, texted, ts FROM calls WHERE business = ? AND ts >= ? AND ts < ?",
                       (business, start, end)).fetchall()
    inbound = db.execute(
        "SELECT caller, body, ts FROM messages WHERE business = ? AND direction = 'in' AND ts >= ? AND ts < ? "
        "ORDER BY ts", (business, start, end)).fetchall()
    leads_rows = {r["caller"]: dict(r) for r in db.execute(
        "SELECT * FROM leads WHERE business = ?", (business,)).fetchall()}

    replied: dict[str, list[str]] = {}
    first_seen: dict[str, float] = {}
    for m in inbound:
        if m["body"].strip().lower() in ("stop", "stopall", "unsubscribe", "cancel", "end", "quit"):
            continue
        replied.setdefault(m["caller"], []).append(m["body"])
        first_seen.setdefault(m["caller"], m["ts"])

    def in_period(ts):
        return ts is not None and start <= ts < end

    leads = []
    for caller, msgs in replied.items():
        row = leads_rows.get(caller, {})
        urgent = in_period(row.get("emergency_notified_at"))
        sent = urgent or in_period(row.get("notified_at"))
        # No-AI mode forwards every reply to the owner, so any reply counts as a lead.
        if sent or biz.get("ai") is False:
            leads.append({"caller": caller, "when": first_seen[caller], "urgent": urgent,
                          "summary": row.get("summary") or "", "first_message": msgs[0]})
    leads.sort(key=lambda x: x["when"])

    opted_out = sum(1 for c in {c["caller"] for c in calls} if leads_rows.get(c, {}).get("opted_out"))
    avg = biz.get("avg_job_value")
    return {
        "business": biz.get("name", business),
        "start": start, "end": end,
        "missed_calls": len(calls),
        "callers": len({c["caller"] for c in calls}),
        "texted": sum(c["texted"] for c in calls),
        "replied": len(replied),
        "leads": leads,
        "urgent": sum(1 for x in leads if x["urgent"]),
        "opted_out": opted_out,
        "avg_job_value": avg,
        "half_booked_value": round(len(leads) * avg / 2) if avg else None,
        "billable": len(leads) >= biz.get("guarantee_min_leads", GUARANTEE_MIN_LEADS),
        "price": biz.get("monthly_price", MONTHLY_PRICE),
    }


def day(ts: float) -> str:
    d = datetime.fromtimestamp(ts)
    return f"{d:%b} {d.day}"


def when(ts: float) -> str:
    d = datetime.fromtimestamp(ts)
    return f"{day(ts)}, {d.strftime('%I:%M %p').lstrip('0')}"


def text_summary(r: dict) -> str:
    n = len(r["leads"])
    lines = [f"{r['business']} missed-call report, {day(r['start'])} to {day(r['end'] - 1)}:",
             f"- {r['missed_calls']} missed calls caught, {r['texted']} texted back within seconds",
             f"- {r['replied']} callers texted back",
             f"- {n} lead{'s' if n != 1 else ''} sent to you" + (f" ({r['urgent']} urgent)" if r["urgent"] else "")]
    if r["half_booked_value"]:
        lines.append(f"- If half of those booked at your ~${r['avg_job_value']:,} average job: "
                     f"~${r['half_booked_value']:,}")
    return "\n".join(lines)


def render_html(r: dict) -> str:
    e = html.escape
    n = len(r["leads"])
    def details(x):
        text = x["summary"] or x["first_message"][:200]
        return "\n".join(line for line in text.splitlines() if not line.endswith(": ?"))

    rows = "".join(
        f"<tr><td>{e(when(x['when']))}</td><td>{'<b class=u>URGENT</b><br>' if x['urgent'] else ''}"
        f"{e(details(x)).replace(chr(10), '<br>')}</td></tr>"
        for x in r["leads"]) or "<tr><td colspan=2>No leads in this period.</td></tr>"
    value = ""
    if r["half_booked_value"]:
        value = (f"<div class='box wide'><div class=big>~${r['half_booked_value']:,}</div>if half of these leads booked "
                 f"at your ~${r['avg_job_value']:,} average job</div>")
    verdict = (f"{n} leads this period, so it more than covered the ${r['price']}/month."
               if r["billable"] and r["half_booked_value"] and r["half_booked_value"] > r["price"]
               else f"{n} leads this period." if r["billable"]
               else f"Fewer than {GUARANTEE_MIN_LEADS} leads this period, so under the slow-month guarantee "
                    "you don't pay for it.")
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Missed-call report: {e(r['business'])}</title>
<style>
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;max-width:760px;margin:24px auto;padding:0 16px;color:#1d2433;background:#fff}}
h1{{margin:0 0 4px;font-size:26px}} .muted{{color:#5b6475}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0}}
.wide{{grid-column:1/-1}} .box{{border:1.5px solid #dfe3ea;border-radius:12px;padding:14px}} .big{{font-size:30px;font-weight:800;color:#0b6bcb}}
table{{width:100%;border-collapse:collapse;margin-top:8px}} td{{border-top:1px solid #dfe3ea;padding:10px 6px;vertical-align:top}}
td:first-child{{white-space:nowrap;color:#5b6475;width:1%}} .u{{color:#c62828}}
.verdict{{background:#eef6ff;border-radius:12px;padding:14px;margin:16px 0;font-weight:600}}
</style></head><body>
<h1>{e(r['business'])}: missed-call report</h1>
<div class=muted>{e(day(r['start']))} to {e(day(r['end'] - 1))}</div>
<div class=grid>
<div class=box><div class=big>{r['missed_calls']}</div>missed calls caught</div>
<div class=box><div class=big>{r['texted']}</div>texted back within seconds</div>
<div class=box><div class=big>{r['replied']}</div>callers texted back</div>
<div class=box><div class=big>{n}</div>leads sent to you{f" ({r['urgent']} urgent)" if r['urgent'] else ""}</div>
{value}
</div>
<div class=verdict>{e(verdict)}</div>
<h2>Every lead</h2>
<table>{rows}</table>
<p class=muted>Without this, most of these callers would have hit voicemail, and most people who hit voicemail
call the next company instead of leaving a message.{f" {r['opted_out']} caller(s) replied STOP and weren't texted again." if r['opted_out'] else ""}</p>
</body></html>"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--business", required=True, help="the client's Twilio number (key in clients.json)")
    ap.add_argument("--start", help="YYYY-MM-DD (default: 30 days ago)")
    ap.add_argument("--end", help="YYYY-MM-DD, inclusive (default: today)")
    ap.add_argument("--db", default=os.getenv("DB_PATH", ROOT / "leads.db"))
    ap.add_argument("--clients", default=os.getenv("CLIENTS_FILE", ROOT / "clients.json"))
    ap.add_argument("--out", default=ROOT / "reports")
    a = ap.parse_args()

    biz = json.loads(Path(a.clients).read_text()).get(a.business)
    if not biz:
        raise SystemExit(f"{a.business} isn't in {a.clients}")
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_day = datetime.strptime(a.end, "%Y-%m-%d") if a.end else today
    start_day = datetime.strptime(a.start, "%Y-%m-%d") if a.start else end_day - timedelta(days=29)
    start, end = start_day.timestamp(), (end_day + timedelta(days=1)).timestamp()

    r = build(a.db, a.business, biz, start, min(end, time.time() + 1))
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    slug = "".join(c if c.isalnum() else "-" for c in r["business"].lower()).strip("-")
    path = out / f"{slug}-{start_day:%Y-%m-%d}-to-{end_day:%Y-%m-%d}.html"
    path.write_text(render_html(r), encoding="utf-8")
    print(text_summary(r))
    print(f"\nReport: {path}")


if __name__ == "__main__":
    main()
