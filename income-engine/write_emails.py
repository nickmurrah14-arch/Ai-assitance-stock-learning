"""Step 3: draft a short personalized email per lead with Claude.

Drafts land in data/drafts.csv with status=draft. Read them, fix anything off,
and change status to "approved" for the ones you want sent.

    python write_emails.py [--limit 40] [--min-issues 2]
"""
import argparse
import json

import anthropic

import config
from csvio import read_rows, write_rows

SYSTEM = """You write short cold emails from a small local automation studio to owners of local service businesses.

Rules:
- 60 to 110 words in the body. Plain text, no links except the booking link if one is given, no images, no emojis, no markdown.
- Open with one specific, true observation taken from the audit findings. Never invent facts beyond the data given.
- Connect that observation to money the owner is losing (missed calls, slow replies, lost quotes) in one sentence.
- One sentence on the offer. One low-friction ask (reply "yes" / a 10 minute call). No pressure, no fake urgency, no hype words.
- Sound like a real person writing one email, not a marketer. If the sender's city is given and near the business, mention being local once, naturally (e.g. \"I'm in Deltona\").
- Subject line: 2 to 6 words, lowercase is fine, no clickbait, no "Re:" or "Fwd:" tricks.
- Do not add a signature or unsubscribe line; those are appended automatically."""

SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string"},
    },
    "required": ["subject", "body"],
    "additionalProperties": False,
}


def footer() -> str:
    sig = [s for s in (config.SENDER_NAME, config.SENDER_COMPANY, config.SENDER_POSTAL_ADDRESS) if s]
    optout = "Not interested? Reply \"stop\" and you won't hear from me again."
    return "\n" + "\n".join(sig) + "\n\n" + optout


def draft(client: anthropic.Anthropic, lead: dict) -> dict:
    facts = {
        "business_name": lead["name"],
        "category": lead.get("category", ""),
        "city_address": lead.get("address", ""),
        "google_rating": lead.get("rating", ""),
        "google_review_count": lead.get("reviews", ""),
        "audit_findings": lead.get("issues", "").split(" | "),
    }
    prompt = (
        f"Our offer: {config.OFFER}\n"
        f"Booking link (optional to include): {config.BOOKING_LINK or 'none'}\n"
        f"Sender first name: {config.SENDER_NAME.split(' ')[0] if config.SENDER_NAME else 'unknown'}\n"
        f"Sender is based in: {config.SENDER_CITY or 'not stated - do not claim to be local'}\n\n"
        f"Lead data:\n{json.dumps(facts, indent=2)}"
    )
    extra = {}
    if config.ANTHROPIC_MODEL in ("claude-opus-5", "claude-fable-5-1"):
        # If the model declines, re-run on Anthropic's recommended fallback model.
        extra = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
    response = client.beta.messages.create(
        model=config.ANTHROPIC_MODEL,
        max_tokens=2000,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
        **extra,
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("model declined this request")
    text = next(b.text for b in response.content if b.type == "text")
    data = json.loads(text)
    return {"subject": data["subject"].strip(), "body": data["body"].strip() + "\n" + footer()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--min-issues", type=int, default=2, help="skip businesses that already look well set up")
    args = ap.parse_args()
    missing = [k for k in ("SENDER_NAME", "SENDER_POSTAL_ADDRESS") if not getattr(config, k)]
    if missing:
        raise SystemExit(f"Set {', '.join(missing)} in income-engine/.env (CAN-SPAM needs a real postal address)")

    suppressed = set(config.SUPPRESSION.read_text().split()) if config.SUPPRESSION.exists() else set()
    drafts = read_rows(config.DRAFTS_CSV)
    already = {d["place_id"] for d in drafts}
    candidates = [
        r for r in read_rows(config.AUDITED_CSV)
        if r.get("email")
        and r["place_id"] not in already
        and int(r.get("issue_count") or 0) >= args.min_issues
        and r["email"] not in suppressed
        and r["email"].split("@")[1] not in suppressed
    ]
    # Most-fixable first: more issues, but an established business (has reviews) that can pay.
    candidates.sort(key=lambda r: (int(r["issue_count"]), min(int(r.get("reviews") or 0), 100)), reverse=True)

    client = anthropic.Anthropic()
    for lead in candidates[: args.limit]:
        try:
            d = draft(client, lead)
        except (anthropic.APIError, RuntimeError, json.JSONDecodeError) as e:
            print(f"skip {lead['name']}: {e}")
            continue
        drafts.append(
            {
                "place_id": lead["place_id"],
                "name": lead["name"],
                "email": lead["email"],
                "subject": d["subject"],
                "body": d["body"],
                "status": "draft",
            }
        )
        write_rows(config.DRAFTS_CSV, drafts)
        print(f"drafted: {lead['name']} <{lead['email']}> - {d['subject']}")
    print(f"Review {config.DRAFTS_CSV} and set status=approved on the ones to send.")


if __name__ == "__main__":
    main()
