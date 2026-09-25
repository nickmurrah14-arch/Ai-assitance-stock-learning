# Lead Responder: missed-call text-back + AI texting for HVAC & plumbing

This is the product you sell. When a customer's call goes unanswered:

1. **Within seconds** they get a text: *"Hi, this is Acme Heating & Plumbing. Sorry we missed your call! I'm our automated assistant. What can we help you with today?"*
2. **An AI assistant (Claude) texts with them.** It collects their name, address, problem and availability, answers basic questions using only the business's facts, and handles emergencies safely (gas smell → leave and call 911).
3. **The owner gets a text** with the finished lead summary, or an **URGENT** alert right away for emergencies.

```
Customer calls ─► nobody answers ─► Twilio number ─► auto-text ─► AI conversation ─► owner gets the lead
```

Safety and compliance are built in: STOP/START opt-out, an automated-assistant disclosure, one text per missed call (no spam when someone calls 5 times), a cap of 15 AI replies per customer per day, and a polite fallback plus owner alert if the AI is down. Twilio webhook signatures are verified.

## Try it now (no Twilio needed)

```bash
cd lead-responder
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python simulate.py        # you play the customer; the texts and owner alerts print in the terminal
```

Screen-record this for your **sales demo video**. Try "my AC stopped working", then "I smell gas".

## Going live

### 1. Twilio (about $20 to start)
1. Create a Twilio account and upgrade it ($20 minimum top-up). Buy a **local number** in your area ($1.15/mo).
2. **Register for business texting (A2P 10DLC).** US carriers block unregistered business texts.
   - For your own demo number: sole-proprietor brand (~$4 one-time) + campaign vetting (~$15).
   - For each client: register **their** business as its own brand under your account (Twilio's "ISV" setup: Trust Hub → secondary customer profile). Public for-profit brands also pay a ~$12.50 authentication fee, plus a small monthly campaign fee. Approval takes days to 2 weeks, so start on day 1. ([Twilio A2P docs](https://www.twilio.com/docs/trust-hub/registrations/a2p-10dlc-campaign), [fees](https://www.sociocs.com/post/twilio-10dlc-explained/))
   - Campaign use case: "Customer care" / "Mixed". Sample message: the first-text above. Opt-in description: "Customer called the business; we text back the number that called."
3. On the number, set **Voice → A call comes in** to `POST https://YOUR-APP/voice` and **Messaging → A message comes in** to `POST https://YOUR-APP/sms`.

### 2. Host the app (~$5/mo)
Any always-on host works. Don't use a free tier that sleeps, because Twilio gives up after 15 seconds. It needs HTTPS and a persistent disk for the SQLite file.
- **Easiest:** Railway or Render (paid tier) with a volume, start command `gunicorn -w 1 --threads 8 -b 0.0.0.0:$PORT wsgi:app`.
- **Cheapest:** a $4–6/mo VPS with Caddy in front for automatic HTTPS.

Set the environment variables from `.env.example`, and create `clients.json` from `clients.example.json`, keyed by each client's Twilio number. Check `https://YOUR-APP/health`.

### 3. Connect each client's phone (pick one)
- **Mode B, keep their number (most common):** set up *conditional call forwarding* on the business line so unanswered or busy calls forward to their Twilio number. Codes usually are: **AT&T / T-Mobile** `**61*<twilio number>#` (no answer) and `**67*<twilio number>#` (busy); **Verizon** `*71<twilio number>`. VoIP systems (RingCentral, Google Voice, Grasshopper, etc.) have a setting for it. Confirm with their carrier, then test by calling and not answering.
- **Mode A, ring first:** the Twilio number becomes the published number (Google Business Profile, website). Add `"forward_to": "+1owner..."` in `clients.json`, and it rings the owner's cell for `ring_seconds` (default 20) before texting. Keep `ring_seconds` shorter than the owner's voicemail pickup, or voicemail will "answer" and no text goes out.

### 4. Onboarding checklist per client (about 45 minutes)
- [ ] Fill in their `clients.json` entry: name, owner_cell, service area, hours, services, emergency policy, callback time. The AI only states these facts, so get them right.
- [ ] Buy their Twilio number and submit their A2P brand + campaign.
- [ ] Set up call forwarding, then call from your phone without answering. Check that you get the text and the owner gets the alert.
- [ ] Run `simulate.py --business +1THEIRNUMBER` through 3 scenarios (routine repair, new install quote, emergency).

## Costs and pricing

| Per client, per month | Cost |
|---|---|
| Twilio number | $1.15 |
| Texts (~300 segments incl. carrier fees ~1.1¢ each) | ~$3–4 |
| A2P campaign fee | a few $ |
| Claude API (~100 AI replies at ~1–2¢) | ~$1–3 |
| Your hosting, shared across all clients | ~$5 total |
| **Your cost** | **~$10–15** |

**Suggested price:** **$497 setup** (covers the ~$20–35 in registration fees and your onboarding time) + **$197/mo**. That's about $180/mo profit per client. For comparison, an answering service runs $100–500/mo and a part-time receptionist $1,500–2,500/mo.

**Pitch math for the owner:** "The average HVAC repair is a few hundred dollars, and an install is several thousand. If this saves one job a month, it pays for itself many times over."

## No-AI mode (cheapest, and a free live demo)

Set `"ai": false` on a client in `clients.json`. Missed callers still get the instant text, but every reply is forwarded to the owner, and the customer gets one fixed auto-reply (`"simple_reply"`, optional). It makes no Claude calls, so it's free to run apart from Twilio. Use it for the $150 Fiverr basic package, or to demo live with just a Twilio free trial.

## Tests

```bash
python -m unittest discover -s tests
```

## Files

| File | What it does |
|---|---|
| `responder.py` | Core logic: missed call, conversation, owner alerts, opt-out, limits |
| `brain.py` | Claude prompt + structured output (reply + lead fields + emergency flag) |
| `app.py` / `wsgi.py` | Twilio webhooks (`/voice`, `/voice/after`, `/sms`, `/health`) |
| `store.py` | SQLite storage for conversations and lead state |
| `simulate.py` | Terminal demo, no Twilio needed |
