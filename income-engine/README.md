# Income Engine

An automated pipeline that finds local businesses, audits their websites, drafts a personalized email for each with Claude, and sends it plus one follow-up, slowly and legally.

Read **[PLAYBOOK.md](PLAYBOOK.md)** first. It covers what to sell, pricing, the research behind it, and the legal and deliverability rules.

## Setup

```bash
cd income-engine
pip install -r requirements.txt
cp .env.example .env   # fill in API keys, your name, postal address, offer, SMTP
```

## Daily run

```bash
python find_leads.py --file targets/deltona-hvac-plumbing.txt   # -> data/leads.csv (or pass queries directly)
python audit_sites.py                      # -> data/audited.csv + data/call_list.csv (no email found: phone them yourself)
python write_emails.py --limit 40          # -> data/drafts.csv, status=draft
#   open data/drafts.csv, edit anything off, set status=approved on the good ones
python send_emails.py                      # dry run
python send_emails.py --send               # send approved drafts (daily limit applies)
python send_emails.py --followups --send   # bump non-repliers after 4 days
```

When someone replies, change their row in `data/drafts.csv` to `status=replied`. If they asked to stop, also add their email to `data/suppression.txt`.

## Dropshipping calculator

Check whether a product can make money after ads before you spend on it (see PLAYBOOK §7):

```bash
python dropship_calc.py --price 1200 --cost 780 --cpa 90
```

## Tests

```bash
python -m unittest discover -s tests
```

## Notes

- Nothing sends without `--send`, and only rows you marked `approved` go out.
- `data/` and `.env` are git-ignored, so leads and keys never get committed.
- Default model is `claude-opus-5` with low effort. Set `ANTHROPIC_MODEL=claude-sonnet-5` in `.env` to cut cost per email.
