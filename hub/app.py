"""Business HQ: a local dashboard for calls, email drafts, the cheat sheet and guides.

Runs only on your computer (127.0.0.1). Reads and writes the CSVs in income-engine/data.

    python hub/app.py            # then open http://127.0.0.1:5050
    python hub/app.py --open     # also opens your browser
"""
import argparse
import datetime
import json
import os
import re
import sys
import threading
import webbrowser
from pathlib import Path

import markdown
from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "income-engine"))
import config  # noqa: E402  (also loads income-engine/.env)
from csvio import append_row, read_rows, write_rows  # noqa: E402

PLAYBOOK = json.loads((Path(__file__).parent / "playbook.json").read_text(encoding="utf-8"))
OUTCOMES = ["No answer", "Left voicemail", "Call back", "Interested - demo booked",
            "Not interested", "Wrong number", "Do not contact"]
CLOSED = {"Not interested", "Wrong number", "Do not contact"}
GUIDES = {
    "start-here": ("Start here", ROOT / "START-HERE.md"),
    "sales-kit": ("Sales kit", ROOT / "sales" / "SALES-KIT.md"),
    "playbook": ("Business playbook & research", ROOT / "income-engine" / "PLAYBOOK.md"),
    "product": ("The product: setup & pricing", ROOT / "lead-responder" / "README.md"),
    "pipeline": ("Lead pipeline commands", ROOT / "income-engine" / "README.md"),
}


def call_sheet_path() -> Path:
    return config.DATA / "call_sheet.csv"


def call_log_path() -> Path:
    return config.DATA / "call_log.csv"


def key_of(row: dict) -> str:
    return row.get("place_id") or re.sub(r"[^a-z0-9]+", "-", row["name"].lower()).strip("-")


def today() -> str:
    return datetime.date.today().isoformat()


def personalize(text: str) -> str:
    name = config.SENDER_NAME.split(" ")[0] if config.SENDER_NAME else ""
    return text.replace("[your name]", name) if name else text


def bucket(row: dict) -> str:
    result = row.get("result", "")
    if result in CLOSED:
        return "closed"
    if result == "Interested - demo booked":
        return "interested"
    if row.get("follow_up_date") and row["follow_up_date"] <= today():
        return "due"
    if row.get("follow_up_date"):
        return "later"
    return "to_call"


def create_app() -> Flask:
    app = Flask(__name__)
    app.jinja_env.filters["personalize"] = personalize

    @app.context_processor
    def globals_():
        return {"biz_name": PLAYBOOK["business_name"], "today": today()}

    @app.get("/")
    def home():
        rows = read_rows(call_sheet_path())
        drafts = read_rows(config.DRAFTS_CSV)
        counts = {b: sum(1 for r in rows if bucket(r) == b) for b in ("to_call", "due", "interested", "closed", "later")}
        draft_counts = {s: sum(1 for d in drafts if d["status"] == s) for s in ("draft", "approved", "sent", "replied")}
        leads_total = len(read_rows(config.DATA / "fl_licensees.csv"))
        return render_template("home.html", counts=counts, total=len(rows), draft_counts=draft_counts,
                               leads_total=leads_total, due=[r for r in rows if bucket(r) == "due"][:10],
                               key_of=key_of)

    @app.get("/calls")
    def calls():
        view = request.args.get("view", "to_call")
        rows = read_rows(call_sheet_path())
        shown = rows if view == "all" else [r for r in rows if bucket(r) == view]
        return render_template("calls.html", rows=shown, view=view, key_of=key_of, bucket=bucket)

    @app.get("/call/<key>")
    def call(key):
        rows = read_rows(call_sheet_path())
        idx = next((i for i, r in enumerate(rows) if key_of(r) == key), None)
        if idx is None:
            abort(404)
        row = rows[idx]
        queue = [r for r in rows if bucket(r) in ("to_call", "due") and key_of(r) != key]
        noticed = [x.strip() for x in re.split(r"[|;]", row.get("what_we_noticed", "")) if x.strip()]
        history = [h for h in read_rows(call_log_path()) if h.get("key") == key]
        return render_template("call.html", row=row, key=key, noticed=noticed, history=history,
                               next_key=key_of(queue[0]) if queue else None, pb=PLAYBOOK, outcomes=OUTCOMES,
                               ai_enabled=bool(os.getenv("ANTHROPIC_API_KEY")),
                               default_followup=(datetime.date.today() + datetime.timedelta(days=2)).isoformat())

    @app.post("/call/<key>/log")
    def log_call(key):
        rows = read_rows(call_sheet_path())
        row = next((r for r in rows if key_of(r) == key), None)
        if row is None:
            abort(404)
        result = request.form.get("result", "")
        if result not in OUTCOMES:
            abort(400)
        notes = request.form.get("notes", "").strip()
        follow = request.form.get("follow_up_date", "") if result not in CLOSED else ""
        now = datetime.datetime.now().isoformat(timespec="minutes")
        row["result"] = result
        row["follow_up_date"] = follow
        row["last_called"] = now
        row["attempts"] = str(int(row.get("attempts") or 0) + 1)
        if notes:
            row["notes_from_calls"] = (row.get("notes_from_calls", "") + f" [{now[:10]}] {notes}").strip()
        write_rows(call_sheet_path(), rows)
        append_row(call_log_path(), {"time": now, "key": key, "name": row["name"], "phone": row.get("phone", ""),
                                     "result": result, "notes": notes, "follow_up_date": follow})
        nxt = request.form.get("next")
        return redirect(url_for("call", key=nxt) if nxt else url_for("calls"))

    @app.post("/api/suggest")
    def suggest():
        """Optional live helper. Only works if ANTHROPIC_API_KEY is set (each suggestion costs ~1-2 cents)."""
        if not os.getenv("ANTHROPIC_API_KEY"):
            return jsonify(error="Add ANTHROPIC_API_KEY to income-engine/.env to turn this on."), 400
        import anthropic

        data = request.get_json(force=True)
        model = os.getenv("ANTHROPIC_MODEL", "claude-opus-5")
        system = ("You coach a local salesperson live on a phone call. They sell a missed-call text-back "
                  "service to HVAC and plumbing companies. The offer: " + PLAYBOOK["offer"]["one_liner"] + " "
                  + " ".join(PLAYBOOK["offer"]["points"]) + " It goes live after carrier texting approval, "
                  "usually 1-2 weeks. "
                  "They are new and have no other clients yet; never invent clients, results or features. "
                  "Given what the prospect just said, reply with ONE thing to say next: 1-3 short, natural "
                  "sentences, then a line starting 'Tip:' with one short coaching note. Plain text only.\n\n"
                  "Approved answers you can draw on:\n" + json.dumps(PLAYBOOK["faq"] + PLAYBOOK["objections"]))
        extra = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"} \
            if model in ("claude-opus-5", "claude-fable-5-1") else {}
        client = anthropic.Anthropic()
        try:
            resp = client.beta.messages.create(
                model=model, max_tokens=1000, system=system,
                messages=[{"role": "user", "content":
                           f"Business: {data.get('business', '')}\nWhat we noticed: {data.get('noticed', '')}\n"
                           f"The prospect just said: {data.get('said', '')}"}],
                output_config={"effort": "low"}, **extra)
        except anthropic.APIError as e:
            return jsonify(error=f"AI helper error: {e}"), 502
        if resp.stop_reason == "refusal":
            return jsonify(error="The AI declined; use the cheat sheet answers."), 502
        return jsonify(text="".join(b.text for b in resp.content if b.type == "text").strip())

    @app.get("/drafts")
    def drafts():
        rows = read_rows(config.DRAFTS_CSV)
        status = request.args.get("status", "draft")
        shown = rows if status == "all" else [d for d in rows if d["status"] == status]
        return render_template("drafts.html", rows=shown, status=status)

    @app.post("/drafts/<place_id>/status")
    def set_draft_status(place_id):
        new = request.form.get("status")
        if new not in ("draft", "approved", "skip"):
            abort(400)
        rows = read_rows(config.DRAFTS_CSV)
        for d in rows:
            if d["place_id"] == place_id and d["status"] in ("draft", "approved", "skip"):
                d["status"] = new
        write_rows(config.DRAFTS_CSV, rows)
        return redirect(url_for("drafts", status=request.form.get("back", "draft")))

    @app.get("/cheatsheet")
    def cheatsheet():
        return render_template("cheatsheet.html", pb=PLAYBOOK, standalone=False)

    @app.get("/guides")
    def guides():
        return render_template("guides.html", guides=GUIDES)

    @app.get("/guides/<slug>")
    def guide(slug):
        if slug not in GUIDES:
            abort(404)
        title, path = GUIDES[slug]
        body = path.read_text(encoding="utf-8") if path.exists() else "Not found on this computer."
        html = markdown.markdown(body, extensions=["tables", "fenced_code"])
        return render_template("guide.html", title=title, html=html, path=str(path))

    return app


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5050)
    ap.add_argument("--open", action="store_true", help="open the dashboard in your browser")
    args = ap.parse_args()
    url = f"http://127.0.0.1:{args.port}"
    if args.open:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    print(f"Business HQ running at {url}  (close this window to stop)")
    create_app().run(host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
