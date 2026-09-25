import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audit_sites import analyze_html, find_emails, issues_for  # noqa: E402

OLD_SITE = """<html><head><title>Bob's Plumbing</title></head>
<body>Call us! <a href="mailto:bob@bobsplumbing.com">email</a>
<img src="logo@2x.png"> contact: someone@example.com
<footer>&copy; 2019 Bob's Plumbing</footer></body></html>"""

MODERN_SITE = """<html><head><meta name="viewport" content="width=device-width"></head>
<body><form action="/quote"></form><a href="https://calendly.com/x">Book now</a>
<script src="https://embed.tawk.to/abc"></script><footer>© 2026 Co</footer></body></html>"""


class AuditTests(unittest.TestCase):
    def test_old_site_flags_problems(self):
        a = analyze_html(OLD_SITE, "http://bobsplumbing.com")
        self.assertFalse(a["https"])
        self.assertFalse(a["mobile_viewport"])
        self.assertFalse(a["has_form"])
        self.assertFalse(a["online_booking"])
        self.assertEqual(a["copyright_year"], 2019)
        issues = issues_for({"website": "http://bobsplumbing.com", "reviews": "8"}, a)
        self.assertTrue(any("book" in i for i in issues))
        self.assertTrue(any("2019" in i for i in issues))
        self.assertTrue(any("8 Google reviews" in i for i in issues))

    def test_modern_site_is_clean(self):
        a = analyze_html(MODERN_SITE, "https://co.com")
        self.assertTrue(a["mobile_viewport"] and a["has_form"] and a["online_booking"] and a["chat_widget"])
        self.assertEqual(issues_for({"website": "https://co.com", "reviews": "300"}, a), [])

    def test_no_website(self):
        issues = issues_for({"website": ""}, {})
        self.assertEqual(len(issues), 1)
        self.assertIn("no website", issues[0])

    def test_find_emails_filters_junk_and_prefers_own_domain(self):
        html = "x@gmail.com info@acme.com logo@2x.png noreply@acme.com test@example.com"
        self.assertEqual(find_emails(html, "acme.com"), ["info@acme.com", "x@gmail.com"])


if __name__ == "__main__":
    unittest.main()
