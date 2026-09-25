"""Shared settings, loaded from environment variables (see .env.example)."""
import os
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

LEADS_CSV = DATA / "leads.csv"
AUDITED_CSV = DATA / "audited.csv"
CALL_LIST_CSV = DATA / "call_list.csv"  # leads with a phone but no email: call them yourself
DRAFTS_CSV = DATA / "drafts.csv"
SENT_LOG = DATA / "sent_log.csv"
SUPPRESSION = DATA / "suppression.txt"  # one email or domain per line; never contacted


def _load_dotenv():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"'))


_load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
PAGESPEED_API_KEY = os.getenv("PAGESPEED_API_KEY", "")  # optional; raises the free quota
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-5")

# Who you are. CAN-SPAM requires a real postal address and a working opt-out.
SENDER_NAME = os.getenv("SENDER_NAME", "")
SENDER_COMPANY = os.getenv("SENDER_COMPANY", "")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_POSTAL_ADDRESS = os.getenv("SENDER_POSTAL_ADDRESS", "")
SENDER_CITY = os.getenv("SENDER_CITY", "")  # e.g. "Deltona, FL" - local beats anonymous
BOOKING_LINK = os.getenv("BOOKING_LINK", "")

# The offer the emails pitch. Edit to match what you actually deliver.
OFFER = os.getenv(
    "OFFER",
    "We set up an assistant that texts back every missed call within seconds, gets the job "
    "details (name, address, problem, timing) by text, and sends you the lead, 24/7, so callers "
    "don't move on to the next company. Flat setup fee plus a monthly fee; if it doesn't recover "
    "at least one lead in the first 30 days, the setup fee is refunded.",
)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.zoho.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
DAILY_SEND_LIMIT = int(os.getenv("DAILY_SEND_LIMIT", "30"))  # per inbox; ramp 5 -> 30 over ~2 weeks
SECONDS_BETWEEN_SENDS = int(os.getenv("SECONDS_BETWEEN_SENDS", "90"))
