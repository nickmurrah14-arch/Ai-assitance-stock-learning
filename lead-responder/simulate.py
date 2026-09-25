"""Chat with the assistant as if you were a customer. No Twilio needed.

Great for tuning the prompt and for recording the sales demo video.

    python simulate.py                      # uses the first business in clients.json (or the example)
    python simulate.py --business +15551234567
"""
import argparse
import json
import tempfile
from pathlib import Path

from brain import ClaudeBrain
from responder import Responder
from store import Store

ROOT = Path(__file__).parent
CUSTOMER = "+15550001111"


class PrintSender:
    def __init__(self, owner: str):
        self.owner = owner

    def send(self, from_: str, to: str, body: str) -> None:
        who = "OWNER ALERT" if to == self.owner else "Text to customer"
        print(f"\n[{who}]\n{body}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--business", help="Twilio number key in clients.json")
    args = ap.parse_args()
    path = ROOT / "clients.json"
    clients = json.loads((path if path.exists() else ROOT / "clients.example.json").read_text())
    business = args.business or next(iter(clients))
    biz = clients[business]

    db = Path(tempfile.mkdtemp()) / "sim.db"
    r = Responder(Store(db), ClaudeBrain(), PrintSender(biz.get("owner_cell", "")), clients)
    print(f"Simulating a missed call to {biz['name']}. Type as the customer; Ctrl+C to quit.")
    r.missed_call(business, CUSTOMER)
    try:
        while True:
            msg = input("You: ").strip()
            if msg:
                r.incoming_sms(business, CUSTOMER, msg)
    except (KeyboardInterrupt, EOFError):
        print()


if __name__ == "__main__":
    main()
