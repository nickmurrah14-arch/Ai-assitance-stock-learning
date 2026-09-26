import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import report  # noqa: E402
from test_responder import BIZ, CLIENTS, make  # noqa: E402


class ReportTests(unittest.TestCase):
    def test_counts_calls_replies_and_leads(self):
        r, _, _ = make([{"reply": "Got it", "customer_name": "Maria", "problem": "AC warm",
                         "ready_for_owner": True},
                        {"reply": "Leave now and call 911", "is_emergency": True}])
        r.missed_call(BIZ, "+15550000001")
        r.missed_call(BIZ, "+15550000001")          # repeat call: logged, not re-texted
        r.incoming_sms(BIZ, "+15550000001", "my AC is blowing warm")
        r.missed_call(BIZ, "+15550000002")
        r.incoming_sms(BIZ, "+15550000002", "I smell gas")
        r.missed_call(BIZ, "+15550000003")          # never replied
        biz = {**CLIENTS[BIZ], "avg_job_value": 400}
        rep = report.build(r.store.path, BIZ, biz, time.time() - 60, time.time() + 60)
        self.assertEqual((rep["missed_calls"], rep["callers"], rep["texted"], rep["replied"]), (4, 3, 3, 2))
        self.assertEqual(len(rep["leads"]), 2)
        self.assertEqual(rep["urgent"], 1)
        self.assertTrue(rep["billable"])
        self.assertEqual(rep["half_booked_value"], 400)
        self.assertIn("Maria", report.render_html(rep))
        self.assertIn("4 missed calls caught", report.text_summary(rep))

    def test_slow_month_is_free(self):
        r, _, _ = make()
        r.missed_call(BIZ, "+15550000001")
        rep = report.build(r.store.path, BIZ, CLIENTS[BIZ], time.time() - 60, time.time() + 60)
        self.assertFalse(rep["billable"])
        self.assertIn("slow-month guarantee", report.render_html(rep))


if __name__ == "__main__":
    unittest.main()
