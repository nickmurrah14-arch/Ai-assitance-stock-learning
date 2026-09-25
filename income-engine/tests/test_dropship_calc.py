import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dropship_calc import economics, verdict  # noqa: E402


class DropshipCalcTests(unittest.TestCase):
    def test_cheap_imported_product_loses_money(self):
        e = economics(price=35, cost=12, shipping=6, duty=0.25, cpa=40)
        self.assertLess(e["profit_per_order"], 0)
        self.assertIn("LOSES MONEY", verdict(e["breakeven_cpa"], 40))

    def test_high_ticket_us_product_is_viable(self):
        e = economics(price=1200, cost=780, cpa=90)
        # 1200 - 780 - (34.80 + 0.30) fees - 12 returns - 12 chargebacks = 360.90
        self.assertAlmostEqual(e["breakeven_cpa"], 360.90, places=2)
        self.assertAlmostEqual(e["profit_per_order"], 270.90, places=2)
        self.assertIn("VIABLE", verdict(e["breakeven_cpa"], 90))

    def test_thin_margin(self):
        self.assertIn("THIN", verdict(100, 80))


if __name__ == "__main__":
    unittest.main()
