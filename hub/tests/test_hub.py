import sys
import tempfile
import unittest
from pathlib import Path

HUB = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HUB))

import app as hub  # noqa: E402
from csvio import read_rows, write_rows  # noqa: E402

CALLS = [
    {"place_id": "A1", "priority": "1", "name": "Alpha Air", "city": "Deltona", "phone": "(386) 555-0100",
     "website": "", "email_draft_ready": "", "what_we_noticed": "no website; closed weekends",
     "opener": "Do you ever miss calls?", "result": "", "follow_up_date": ""},
    {"place_id": "B2", "priority": "2", "name": "Beta Plumbing", "city": "DeBary", "phone": "(386) 555-0101",
     "website": "https://beta.example", "email_draft_ready": "yes", "what_we_noticed": "no contact form",
     "opener": "Do you ever miss calls?", "result": "", "follow_up_date": ""},
]


class HubTests(unittest.TestCase):
    def setUp(self):
        d = Path(tempfile.mkdtemp())
        hub.config.DATA = d
        hub.config.DRAFTS_CSV = d / "drafts.csv"
        write_rows(d / "call_sheet.csv", [dict(r) for r in CALLS])
        write_rows(d / "drafts.csv", [{"place_id": "B2", "name": "Beta Plumbing", "email": "b@beta.example",
                                        "subject": "hi", "body": "Hello\n\n{signature}", "status": "draft"}])
        self.d = d
        self.client = hub.create_app().test_client()

    def test_pages_render(self):
        for url in ("/", "/calls", "/calls?view=all", "/call/A1", "/drafts", "/cheatsheet", "/guides",
                    "/guides/sales-kit"):
            self.assertEqual(self.client.get(url).status_code, 200, url)
        page = self.client.get("/call/A1").get_data(as_text=True)
        self.assertIn("closed weekends", page)
        self.assertIn("tel:(386) 555-0100", page)
        self.assertEqual(self.client.get("/call/nope").status_code, 404)

    def test_logging_a_call_updates_sheet_and_log_and_moves_to_next(self):
        res = self.client.post("/call/A1/log", data={"result": "Call back", "notes": "try Tues",
                                                     "follow_up_date": "2099-01-01", "next": "B2"})
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.headers["Location"].endswith("/call/B2"))
        row = read_rows(self.d / "call_sheet.csv")[0]
        self.assertEqual((row["result"], row["follow_up_date"], row["attempts"]), ("Call back", "2099-01-01", "1"))
        self.assertIn("try Tues", row["notes_from_calls"])
        self.assertEqual(read_rows(self.d / "call_log.csv")[0]["result"], "Call back")
        # Scheduled later -> not in "to call" anymore
        self.assertNotIn("Alpha Air", self.client.get("/calls?view=to_call").get_data(as_text=True))

    def test_closed_outcome_clears_follow_up_and_bad_outcome_rejected(self):
        self.client.post("/call/A1/log", data={"result": "Not interested", "follow_up_date": "2099-01-01"})
        self.assertEqual(read_rows(self.d / "call_sheet.csv")[0]["follow_up_date"], "")
        self.assertEqual(self.client.post("/call/A1/log", data={"result": "hacked"}).status_code, 400)

    def test_draft_approve_and_skip(self):
        self.client.post("/drafts/B2/status", data={"status": "approved"})
        self.assertEqual(read_rows(self.d / "drafts.csv")[0]["status"], "approved")
        self.client.post("/drafts/B2/status", data={"status": "skip"})
        self.assertEqual(read_rows(self.d / "drafts.csv")[0]["status"], "skip")
        self.assertEqual(self.client.post("/drafts/B2/status", data={"status": "sent"}).status_code, 400)

    def test_ai_helper_off_without_key(self):
        import os
        os.environ.pop("ANTHROPIC_API_KEY", None)
        self.assertEqual(self.client.post("/api/suggest", json={"said": "hi"}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
