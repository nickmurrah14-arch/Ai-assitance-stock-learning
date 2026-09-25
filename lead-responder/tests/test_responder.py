import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("TWILIO_AUTH_TOKEN", "test-token")

import app as app_module  # noqa: E402
from responder import Responder  # noqa: E402
from store import Store  # noqa: E402
from twilio.request_validator import RequestValidator  # noqa: E402

BIZ = "+15551234567"
OWNER = "+15557654321"
CUST = "+15550001111"
CLIENTS = {BIZ: {"name": "Acme Plumbing", "owner_cell": OWNER}}


class FakeSender:
    def __init__(self):
        self.sent = []

    def send(self, from_, to, body):
        self.sent.append((from_, to, body))

    def to(self, number):
        return [b for _, t, b in self.sent if t == number]


class FakeBrain:
    def __init__(self, results):
        self.results = list(results)
        self.calls = 0

    def respond(self, biz, thread):
        self.calls += 1
        r = self.results.pop(0)
        if isinstance(r, Exception):
            raise r
        base = {"customer_name": "", "service_address": "", "problem": "", "availability": "",
                "is_emergency": False, "ready_for_owner": False}
        return {**base, **r}


def make(results=()):
    store = Store(Path(tempfile.mkdtemp()) / "t.db")
    sender, brain = FakeSender(), FakeBrain(results)
    return Responder(store, brain, sender, CLIENTS), sender, brain


class ResponderTests(unittest.TestCase):
    def test_missed_call_texts_customer_and_alerts_owner_once(self):
        r, sender, _ = make()
        self.assertTrue(r.missed_call(BIZ, CUST))
        self.assertIn("Acme Plumbing", sender.to(CUST)[0])
        self.assertIn("STOP", sender.to(CUST)[0])
        self.assertEqual(len(sender.to(OWNER)), 1)
        # Calling again right away doesn't spam them.
        self.assertFalse(r.missed_call(BIZ, CUST))
        self.assertEqual(len(sender.to(CUST)), 1)

    def test_blocked_caller_id_and_unknown_business_are_ignored(self):
        r, sender, _ = make()
        self.assertFalse(r.missed_call(BIZ, "anonymous"))
        self.assertFalse(r.missed_call("+19999999999", CUST))
        self.assertEqual(sender.sent, [])

    def test_conversation_alerts_owner_once_when_lead_is_ready(self):
        r, sender, _ = make([
            {"reply": "What's going on?", "problem": "AC not cooling"},
            {"reply": "Thanks Jo, we'll call you in 15 minutes.", "customer_name": "Jo",
             "service_address": "1 Main St", "problem": "AC not cooling", "availability": "today",
             "ready_for_owner": True},
            {"reply": "You're welcome!", "customer_name": "Jo", "ready_for_owner": True},
        ])
        r.incoming_sms(BIZ, CUST, "my ac isn't cooling")
        r.incoming_sms(BIZ, CUST, "Jo, 1 Main St, anytime today")
        r.incoming_sms(BIZ, CUST, "thanks")
        owner = sender.to(OWNER)
        self.assertEqual(len(owner), 1)
        self.assertIn("1 Main St", owner[0])
        self.assertEqual(len(sender.to(CUST)), 3)

    def test_emergency_alerts_owner_immediately(self):
        r, sender, _ = make([{"reply": "Leave the house and call 911.", "is_emergency": True,
                              "problem": "gas smell"}])
        r.incoming_sms(BIZ, CUST, "i smell gas near the furnace")
        self.assertTrue(sender.to(OWNER)[0].startswith("URGENT"))

    def test_stop_opts_out_and_start_opts_back_in(self):
        r, sender, brain = make([{"reply": "Hi again!"}])
        r.incoming_sms(BIZ, CUST, "STOP")
        r.incoming_sms(BIZ, CUST, "hello?")
        self.assertFalse(r.missed_call(BIZ, CUST))
        self.assertEqual(sender.sent, [])
        self.assertEqual(brain.calls, 0)
        r.incoming_sms(BIZ, CUST, "START")
        self.assertEqual(brain.calls, 1)

    def test_ai_failure_still_replies_and_alerts_owner(self):
        r, sender, _ = make([RuntimeError("api down")])
        reply = r.incoming_sms(BIZ, CUST, "need a plumber")
        self.assertIn("call you back", reply)
        self.assertIn("need a plumber", sender.to(OWNER)[0])

    def test_daily_reply_cap(self):
        r, sender, brain = make([{"reply": f"r{i}"} for i in range(30)])
        for i in range(20):
            r.incoming_sms(BIZ, CUST, f"msg {i}")
        self.assertEqual(brain.calls, 15)


class RecordingResponder:
    def __init__(self):
        self.calls = []
        self.done = threading.Event()

    def missed_call(self, business, caller):
        self.calls.append(("missed", business, caller))
        self.done.set()

    def incoming_sms(self, business, caller, body):
        self.calls.append(("sms", business, caller, body))
        self.done.set()


class WebhookTests(unittest.TestCase):
    def setUp(self):
        self.rec = RecordingResponder()
        self.clients = {BIZ: {"name": "Acme Plumbing"},
                        "+15552223333": {"name": "Ring First Co", "forward_to": OWNER}}
        self.client = app_module.create_app(self.rec, self.clients).test_client()
        app_module.VALIDATE = False

    def tearDown(self):
        app_module.VALIDATE = True

    def test_forwarded_missed_call_says_message_and_texts(self):
        res = self.client.post("/voice", data={"To": BIZ, "From": CUST})
        self.assertIn(b"<Say>", res.data)
        self.assertTrue(self.rec.done.wait(2))
        self.assertEqual(self.rec.calls[0], ("missed", BIZ, CUST))

    def test_ring_first_mode_dials_owner_then_texts_on_no_answer(self):
        res = self.client.post("/voice", data={"To": "+15552223333", "From": CUST})
        self.assertIn(b"<Dial", res.data)
        self.assertEqual(self.rec.calls, [])
        self.client.post("/voice/after", data={"To": "+15552223333", "From": CUST, "DialCallStatus": "completed"})
        self.assertEqual(self.rec.calls, [])
        self.client.post("/voice/after", data={"To": "+15552223333", "From": CUST, "DialCallStatus": "no-answer"})
        self.assertTrue(self.rec.done.wait(2))
        self.assertEqual(self.rec.calls[0][0], "missed")

    def test_sms_webhook_hands_off(self):
        res = self.client.post("/sms", data={"To": BIZ, "From": CUST, "Body": "hi"})
        self.assertEqual(res.status_code, 200)
        self.assertTrue(self.rec.done.wait(2))
        self.assertEqual(self.rec.calls[0], ("sms", BIZ, CUST, "hi"))

    def test_signature_required(self):
        app_module.VALIDATE = True
        data = {"To": BIZ, "From": CUST, "Body": "hi"}
        self.assertEqual(self.client.post("/sms", data=data).status_code, 403)
        sig = RequestValidator(os.environ["TWILIO_AUTH_TOKEN"]).compute_signature("http://localhost/sms", data)
        # validator was built with the token at app creation time
        res = self.client.post("/sms", data=data, headers={"X-Twilio-Signature": sig})
        self.assertEqual(res.status_code, 200)


if __name__ == "__main__":
    unittest.main()
