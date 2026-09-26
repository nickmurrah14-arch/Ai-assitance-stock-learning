"""Step 4: send approved drafts, slowly, from a secondary domain.

Dry run by default. Only rows with status=approved are sent. Respects the daily
limit, the suppression list, and spaces sends out so the inbox looks human.

    python send_emails.py                       # dry run: prints what would go out
    python send_emails.py --send                # actually sends
    python send_emails.py --followups --send    # one short bump, same thread, after 4 days

When someone replies, set their draft's status to "replied" (or add them to
data/suppression.txt if they said stop) so they get no follow-up.

Use a separate domain (e.g. getacmeco.com, not acmeco.com) with SPF, DKIM and
DMARC set up, and warm it for ~2 weeks before sending. See PLAYBOOK.md.
"""
import argparse
import datetime
import smtplib
import time
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

import config
from csvio import append_row, read_rows, write_rows


def sent_today() -> int:
    today = datetime.date.today().isoformat()
    return sum(1 for r in read_rows(config.SENT_LOG) if r["sent_at"].startswith(today))


FOLLOWUP_DAYS = 4
FOLLOWUP_BODY = (
    "Hi again - just floating this back up in case it got buried. "
    "Happy to show you a 2-minute demo on your own business if it's useful. "
    "If not, no worries at all.\n\n{sig}"
)


def build(row: dict, in_reply_to: str = "") -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = formataddr((config.SENDER_NAME, config.SENDER_EMAIL))
    msg["To"] = row["email"]
    msg["Subject"] = ("Re: " if in_reply_to else "") + row["subject"]
    msg["Message-ID"] = make_msgid(domain=config.SENDER_EMAIL.split("@")[-1])
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to
    msg["List-Unsubscribe"] = f"<mailto:{config.SENDER_EMAIL}?subject=unsubscribe>"
    msg.set_content(row["body"].replace("{signature}", signature()))
    return msg


def signature() -> str:
    """Name, company, postal address (CAN-SPAM) and the opt-out line."""
    sig = [s for s in (config.SENDER_NAME, config.SENDER_COMPANY, config.SENDER_POSTAL_ADDRESS) if s]
    return "\n".join(sig) + "\n\nNot interested? Reply \"stop\" and you won't hear from me again."


def followup_queue(drafts: list[dict], suppressed: set[str]) -> list[dict]:
    """Leads sent a first email FOLLOWUP_DAYS+ ago that haven't replied or had a bump."""
    log = read_rows(config.SENT_LOG)
    bumped = {r["email"] for r in log if r.get("kind") == "followup"}
    cutoff = datetime.datetime.now() - datetime.timedelta(days=FOLLOWUP_DAYS)
    status = {d["email"]: d["status"] for d in drafts}
    sig = "\n".join(s for s in (config.SENDER_NAME, config.SENDER_COMPANY, config.SENDER_POSTAL_ADDRESS) if s)
    sig += "\n\nReply \"stop\" and you won't hear from me again."
    out = []
    for r in log:
        e = r["email"]
        if (r.get("kind", "first") == "first" and status.get(e) == "sent" and e not in bumped
                and e not in suppressed and e.split("@")[1] not in suppressed
                and datetime.datetime.fromisoformat(r["sent_at"]) <= cutoff):
            out.append({**r, "body": FOLLOWUP_BODY.format(sig=sig), "in_reply_to": r.get("message_id", "")})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true", help="really send (default is a dry run)")
    ap.add_argument("--followups", action="store_true", help="send follow-ups instead of first emails")
    args = ap.parse_args()

    suppressed = set(config.SUPPRESSION.read_text().split()) if config.SUPPRESSION.exists() else set()
    already_sent = {r["email"] for r in read_rows(config.SENT_LOG)}
    drafts = read_rows(config.DRAFTS_CSV)
    budget = config.DAILY_SEND_LIMIT - sent_today()
    if args.followups:
        queue = followup_queue(drafts, suppressed)[: max(budget, 0)]
    else:
        queue = [
            d for d in drafts
            if d["status"] == "approved"
            and d["email"] not in already_sent
            and d["email"] not in suppressed
            and d["email"].split("@")[1] not in suppressed
        ][: max(budget, 0)]

    if not queue:
        print(f"Nothing to send (daily budget left: {budget}). Approve drafts in {config.DRAFTS_CSV}.")
        return
    if not args.send:
        for d in queue:
            body = d["body"].replace("{signature}", signature())
            print(f"--- would send to {d['email']} ---\nSubject: {d['subject']}\n\n{body}\n")
        print(f"Dry run: {len(queue)} emails. Re-run with --send to send them.")
        return

    for key in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "SENDER_EMAIL", "SENDER_POSTAL_ADDRESS"):
        if not getattr(config, key):
            raise SystemExit(f"Set {key} in income-engine/.env")

    with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
        for i, d in enumerate(queue):
            msg = build(d, d.get("in_reply_to", ""))
            smtp.send_message(msg)
            if not args.followups:
                d["status"] = "sent"
                write_rows(config.DRAFTS_CSV, drafts)
            append_row(
                config.SENT_LOG,
                {"sent_at": datetime.datetime.now().isoformat(timespec="seconds"),
                 "email": d["email"], "name": d["name"], "subject": d["subject"],
                 "kind": "followup" if args.followups else "first",
                 "message_id": msg["Message-ID"]},
            )
            print(f"sent {i + 1}/{len(queue)}: {d['email']}")
            if i + 1 < len(queue):
                time.sleep(config.SECONDS_BETWEEN_SENDS)


if __name__ == "__main__":
    main()
