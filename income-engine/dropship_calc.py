"""Dropshipping unit economics: will this product make money after ads?

    python dropship_calc.py --price 1200 --cost 780 --cpa 90
    python dropship_calc.py --price 35 --cost 12 --shipping 6 --cpa 40 --duty 0.25

CPA = what you expect to pay in ads per sale. Meta ecommerce median is about $38-49
(2026); Google Shopping for high-ticket items is often $50-150. Use your own
numbers once you have them.
"""
import argparse


def economics(price, cost, shipping=0.0, duty=0.0, cpa=0.0, fee_pct=0.029, fee_fixed=0.30,
              return_rate=0.05, return_loss=0.20, chargeback_rate=0.01):
    """Per-order numbers. return_loss = share of price lost on a returned order
    (return freight, restocking, damage). Chargebacks lose the full price."""
    fees = price * fee_pct + fee_fixed
    duties = cost * duty
    returns = price * return_rate * return_loss
    chargebacks = price * chargeback_rate
    before_ads = price - cost - shipping - duties - fees - returns - chargebacks
    profit = before_ads - cpa
    return {
        "payment_fees": fees,
        "duties": duties,
        "returns_reserve": returns,
        "chargeback_reserve": chargebacks,
        "profit_before_ads": before_ads,
        "breakeven_cpa": before_ads,
        "profit_per_order": profit,
        "net_margin": profit / price if price else 0.0,
    }


def verdict(breakeven_cpa: float, cpa: float) -> str:
    if breakeven_cpa <= 0:
        return "LOSES MONEY even with free ads. Drop this product."
    if cpa <= 0:
        return "Enter an expected --cpa to get a verdict."
    ratio = breakeven_cpa / cpa
    if ratio >= 1.5:
        return f"VIABLE: you can afford {ratio:.1f}x your expected ad cost per sale."
    if ratio >= 1.0:
        return f"THIN: only {ratio:.2f}x headroom. One bad week of ads wipes out profit."
    return f"LOSES MONEY: ads cost {cpa / breakeven_cpa:.1f}x what each order can pay for."


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--price", type=float, required=True, help="what the customer pays")
    ap.add_argument("--cost", type=float, required=True, help="what the supplier charges you")
    ap.add_argument("--shipping", type=float, default=0.0, help="shipping you pay per order")
    ap.add_argument("--duty", type=float, default=0.0, help="import duty as a fraction of cost (0 for US suppliers; 0.10-0.54 for imports)")
    ap.add_argument("--cpa", type=float, default=0.0, help="expected ad cost per sale")
    ap.add_argument("--return-rate", type=float, default=0.05)
    ap.add_argument("--goal", type=float, default=3000.0, help="monthly profit target")
    ap.add_argument("--fixed-monthly", type=float, default=100.0, help="Shopify + apps per month")
    a = ap.parse_args()

    e = economics(a.price, a.cost, a.shipping, a.duty, a.cpa, return_rate=a.return_rate)
    print(f"Price ${a.price:,.2f}  Cost ${a.cost:,.2f}  Shipping ${a.shipping:,.2f}")
    for k in ("duties", "payment_fees", "returns_reserve", "chargeback_reserve"):
        print(f"  - {k.replace('_', ' '):<20} ${e[k]:,.2f}")
    print(f"Profit before ads        ${e['profit_before_ads']:,.2f}  (= break-even CPA)")
    print(f"Expected CPA             ${a.cpa:,.2f}")
    print(f"Profit per order         ${e['profit_per_order']:,.2f}  ({e['net_margin']:.1%} net margin)")
    print()
    print(verdict(e["breakeven_cpa"], a.cpa))
    if e["profit_per_order"] > 0:
        orders = (a.goal + a.fixed_monthly) / e["profit_per_order"]
        print(f"To net ${a.goal:,.0f}/mo: ~{orders:,.0f} orders/mo, ~${orders * a.cpa:,.0f}/mo ad spend.")
    if a.cpa > 0:
        # Rough rule: allow ~10 sales' worth of ad spend to learn whether a product works.
        print(f"Suggested test budget: ~${10 * a.cpa + a.fixed_monthly:,.0f}, with a hard stop.")


if __name__ == "__main__":
    main()
