"""Twilio webhooks. Point each client's Twilio number here:

    Voice  "A call comes in"      -> POST {PUBLIC_BASE_URL}/voice
    Messaging "A message comes in" -> POST {PUBLIC_BASE_URL}/sms

Run locally:  flask --app wsgi run --port 5000   (expose with ngrok for testing)
Production:   gunicorn -w 1 --threads 8 -b 0.0.0.0:$PORT wsgi:app
"""
import json
import logging
import os
import threading
from functools import wraps
from pathlib import Path

from flask import Flask, Response, abort, request
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse

from brain import ClaudeBrain
from responder import Responder
from store import Store

ROOT = Path(__file__).parent


def _load_dotenv():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"'))


_load_dotenv()
logging.basicConfig(level=logging.INFO)

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
VALIDATE = os.getenv("VALIDATE_TWILIO_SIGNATURE", "1") != "0"
MISSED_STATUSES = {"no-answer", "busy", "failed", "canceled"}


class TwilioSender:
    def __init__(self):
        self.client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    def send(self, from_: str, to: str, body: str) -> None:
        self.client.messages.create(from_=from_, to=to, body=body)


def load_clients() -> dict[str, dict]:
    path = Path(os.getenv("CLIENTS_FILE", ROOT / "clients.json"))
    return json.loads(path.read_text()) if path.exists() else {}


def create_app(responder: Responder | None = None, clients: dict | None = None) -> Flask:
    app = Flask(__name__)
    clients = clients if clients is not None else load_clients()
    responder = responder or Responder(
        Store(os.getenv("DB_PATH", ROOT / "leads.db")), ClaudeBrain(), TwilioSender(), clients
    )
    validator = RequestValidator(TWILIO_AUTH_TOKEN)

    def twilio_only(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if VALIDATE:
                url = (PUBLIC_BASE_URL + request.full_path.rstrip("?")) if PUBLIC_BASE_URL else request.url
                if not validator.validate(url, request.form, request.headers.get("X-Twilio-Signature", "")):
                    abort(403)
            return view(*args, **kwargs)
        return wrapped

    def background(fn, *args):
        threading.Thread(target=fn, args=args, daemon=True).start()

    def missed(business: str, caller: str) -> Response:
        vr = VoiceResponse()
        biz = clients.get(business, {})
        vr.say(biz.get("missed_call_voice") or
               f"Sorry we missed your call at {biz.get('name', 'our office')}. We're sending you a text right now.")
        vr.hangup()
        background(responder.missed_call, business, caller)
        return Response(str(vr), mimetype="text/xml")

    @app.post("/voice")
    @twilio_only
    def voice():
        business, caller = request.form.get("To", ""), request.form.get("From", "")
        biz = clients.get(business)
        if biz and biz.get("forward_to"):
            # Mode A: this Twilio number is the published number; ring the owner first.
            vr = VoiceResponse()
            vr.dial(biz["forward_to"], timeout=biz.get("ring_seconds", 20), action="/voice/after",
                    caller_id=caller)
            return Response(str(vr), mimetype="text/xml")
        # Mode B: the business's own line forwards unanswered calls here, so every call is a missed call.
        return missed(business, caller)

    @app.post("/voice/after")
    @twilio_only
    def voice_after():
        if request.form.get("DialCallStatus") in MISSED_STATUSES:
            return missed(request.form.get("To", ""), request.form.get("From", ""))
        vr = VoiceResponse()
        vr.hangup()
        return Response(str(vr), mimetype="text/xml")

    @app.post("/sms")
    @twilio_only
    def sms():
        background(responder.incoming_sms, request.form.get("To", ""),
                   request.form.get("From", ""), request.form.get("Body", ""))
        return Response("<Response></Response>", mimetype="text/xml")

    @app.get("/health")
    def health():
        return {"ok": True, "clients": len(clients)}

    return app
