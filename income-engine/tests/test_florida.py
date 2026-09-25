import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from enrich_websites import candidates, matches  # noqa: E402
from florida_leads import business_rows, nice_name  # noqa: E402


def dbpr_row(occ, name, dba, city, county, status="A", lic="CAC1812345"):
    r = [""] * 22
    r[1], r[2], r[3], r[5], r[8], r[10], r[11], r[14], r[15], r[20] = (
        occ, name, dba, "1 MAIN ST", city, "32725", county, status, "01/01/2010", lic)
    return '"' + '","'.join(r) + '"'


class FloridaLeadsTests(unittest.TestCase):
    def test_filters_trade_county_status_and_merges_trades(self):
        lines = [
            dbpr_row("CAC", "DOE, JOHN", "DELTONA HEAT AND AIR INC", "DELTONA", "74", lic="CAC1"),
            dbpr_row("CFC", "DOE, JANE", "DELTONA HEAT AND AIR INC", "DELTONA", "74", lic="CFC2"),
            dbpr_row("CGC", "ROE, RICK", "BUILDER CO", "DELTONA", "74", lic="CGC3"),       # wrong trade
            dbpr_row("CAC", "POE, PAT", "MIAMI AIR", "MIAMI", "13", lic="CAC4"),           # wrong county
            dbpr_row("CFC", "LOE, LEE", "OLD PLUMBING", "SANFORD", "69", "I", lic="CFC5"),  # inactive
            dbpr_row("CFC", "SMITH, SAM", "INDIVIDUAL", "SANFORD", "69", lic="CFC6"),
        ]
        path = Path(tempfile.mkdtemp()) / "x.csv"
        path.write_text("\n".join(lines), encoding="latin-1")
        rows = business_rows(path, {"74", "69"})
        self.assertEqual([r["name"] for r in rows], ["Deltona Heat And Air INC", "Smith, Sam"])
        self.assertEqual(rows[0]["trade"], "AC + plumbing")
        self.assertEqual(rows[1]["is_business_name"], "no")

    def test_nice_name(self):
        self.assertEqual(nice_name("JIM'S PLUMBING, LLC"), "Jim's Plumbing, LLC")

    def test_domain_candidates_and_matching(self):
        self.assertIn("deltonaheatair.com", candidates("Deltona Heat And Air INC"))
        html = "<h1>Deltona Heat and Air</h1> AC repair, Deltona FL (386) 555-1234"
        self.assertTrue(matches(html, "Deltona Heat And Air INC", "Deltona"))
        self.assertFalse(matches("<h1>Jims Plumbing</h1> Austin, Texas", "Jim's Plumbing INC", "Deltona"))
        self.assertFalse(matches("This domain is for sale! plumbing florida", "Cool Force LLC", "Deltona"))


if __name__ == "__main__":
    unittest.main()
