"""Shared settings, loaded from environment variables (see .env.example)."""
import os
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)

LEADS_CSV = DATA / "leads.csv"
AUDITED_CSV = DATA / "audited.csv"
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
BOOKING_LINK = os.getenv("BOOKING_LINK", "")

# The offer the emails pitch. Edit to match what you actually deliver.
OFFER = os.getenv(
    "OFFER",
    "We set up an AI assistant that instantly texts back every missed call and answers "
    "website inquiries 24/7, so leads get a reply in under a minute instead of calling a "
    "competitor. Flat setup fee plus a small monthly fee; first week free.",
)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
DAILY_SEND_LIMIT = int(os.getenv("DAILY_SEND_LIMIT", "30"))  # per inbox; keep low
SECONDS_BETWEEN_SENDS = int(os.getenv("SECONDS_BETWEEN_SENDS", "90"))
