"""Core logic: missed call -> text back -> AI conversation -> alert the owner.

Framework-free so it can be tested and demoed without Twilio.
"""
import logging
import time
from typing import Protocol

from store import Store

log = logging.getLogger("responder")

STOP_WORDS = {"stop", "stopall", "unsubscribe", "cancel", "end", "quit", "revoke", "optout", "opt out"}
START_WORDS = {"start", "unstop", "yes"}
MAX_AI_REPLIES_PER_DAY = 15      # per customer; caps cost and runaway conversations
MISSED_CALL_TEXT_COOLDOWN = 12 * 3600  # don't re-text someone who calls 5 times in a row
BLOCKED_CALLER_IDS = {"", "anonymous", "restricted", "unknown", "+266696687", "+7378742833", "+2562533", "+8656696"}


class Sender(Protocol):
    def send(self, from_: str, to: str, body: str) -> None: ...


class Brain(Protocol):
    def respond(self, biz: dict, thread: list[dict]) -> dict: ...


def first_text(biz: dict) -> str:
    return biz.get("missed_call_text") or (
        f"Hi, this is {biz['name']}. Sorry we missed your call! I'm our automated assistant. "
        "What can we help you with today? Reply STOP to opt out."
    )


def lead_summary(caller: str, r: dict) -> str:
    parts = [
        f"Name: {r.get('customer_name') or '?'}",
        f"Phone: {caller}",
        f"Address: {r.get('service_address') or '?'}",
        f"Problem: {r.get('problem') or '?'}",
        f"Available: {r.get('availability') or '?'}",
    ]
    return "\n".join(parts)


class Responder:
    def __init__(self, store: Store, brain: Brain, sender: Sender, clients: dict[str, dict]):
        self.store, self.brain, self.sender, self.clients = store, brain, sender, clients

    def _text(self, business: str, caller: str, body: str) -> None:
        self.sender.send(business, caller, body)
        self.store.add_message(business, caller, "out", body)

    def _alert_owner(self, business: str, body: str) -> None:
        owner = self.clients[business].get("owner_cell")
        if owner:
            self.sender.send(business, owner, body)

    def missed_call(self, business: str, caller: str) -> bool:
        """Returns True if a text was sent."""
        biz = self.clients.get(business)
        if not biz or caller.strip().lower() in BLOCKED_CALLER_IDS:
            return False
        lead = self.store.lead(business, caller)
        if lead["opted_out"]:
            return False
        if self.store.replies_since(business, caller, time.time() - MISSED_CALL_TEXT_COOLDOWN):
            return False
        self._text(business, caller, first_text(biz))
        if biz.get("alert_every_missed_call", True):
            self._alert_owner(business, f"Missed call from {caller}. Auto-text sent; I'll alert you with details.")
        return True

    def incoming_sms(self, business: str, caller: str, body: str) -> str | None:
        """Returns the reply sent, if any."""
        biz = self.clients.get(business)
        if not biz:
            return None
        word = body.strip().lower()
        if word in STOP_WORDS:
            self.store.add_message(business, caller, "in", body)
            self.store.update_lead(business, caller, opted_out=1)
            return None  # carrier/Twilio sends the opt-out confirmation
        if word in START_WORDS and self.store.lead(business, caller)["opted_out"]:
            self.store.update_lead(business, caller, opted_out=0)
        lead = self.store.lead(business, caller)
        self.store.add_message(business, caller, "in", body)
        if lead["opted_out"]:
            return None
        if self.store.replies_since(business, caller, time.time() - 86400) >= MAX_AI_REPLIES_PER_DAY:
            return None

        try:
            r = self.brain.respond(biz, self.store.thread(business, caller))
        except Exception:  # never leave a customer hanging because the AI call failed
            log.exception("brain failed for %s", caller)
            reply = f"Thanks! Someone from {biz['name']} will call you back shortly."
            self._text(business, caller, reply)
            self._alert_owner(business, f"Lead from {caller} needs a call back. Last message: {body[:200]}")
            return reply

        self._text(business, caller, r["reply"])
        summary = lead_summary(caller, r)
        self.store.update_lead(business, caller, summary=summary)
        now = time.time()
        if r.get("is_emergency") and not lead["emergency_notified_at"]:
            self._alert_owner(business, f"URGENT - possible emergency. Call now.\n{summary}")
            self.store.update_lead(business, caller, emergency_notified_at=now)
        elif r.get("ready_for_owner") and not lead["notified_at"]:
            self._alert_owner(business, f"New lead ready for call back:\n{summary}")
            self.store.update_lead(business, caller, notified_at=now)
        return r["reply"]
