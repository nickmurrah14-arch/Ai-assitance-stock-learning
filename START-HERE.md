# START HERE

Everything lives in one place: **Business HQ**. On Windows, open the **Business HQ** folder on your Desktop and double-click **"1 - Open Business HQ"**. It opens in your browser at http://127.0.0.1:5050 and runs only on your computer.

| Tab | What it's for |
|---|---|
| **Home** | Where things stand: businesses to call, follow-ups due, interested leads, email drafts |
| **📞 Calls** | Your call list, best first. Each business has a page with what we noticed, your script, quick answers, and a place to log the call. |
| **✉️ Email drafts** | Read each email and approve or skip it. Nothing sends until your email domain is set up. |
| **📋 Cheat sheet** | Every question an owner might ask, with answers, plus objections. Printable. |
| **📚 Guides** | The sales kit, the business playbook and research, product setup, and pipeline commands |

## Do today (free)

1. **Make calls** from the Calls tab, starting at the top. Best times: 7–8am, 11:30am–1pm, 4:30–6pm. Log each call before dialing the next.
2. **Practice the demo:** double-click **"3 - Practice the demo"** in the Business HQ folder and play a customer ("my AC stopped working").
3. **Publish the website (free):** first replace the `EDIT` spots in `docs/index.html` with your email and phone. Then go to GitHub repo → Settings → Pages → Deploy from branch → `claude/automated-income-research-fpgwbf`, folder `/docs`.
4. **Post the Fiverr gig and Upwork profile.** The copy is in the Sales kit guide.

## Help during calls

- Keep the business's page open in the Calls tab. Use the **Quick answers** search box, e.g. type "price".
- Or keep a chat with Claude open and type what they said. You'll get a suggested reply for free.
- Optional: add an Anthropic API key to `income-engine/.env` and a **Suggest a reply** box appears on each call page (about 1–2¢ per suggestion).

## Before any email goes out (~$12)

1. Buy a domain (~$11/yr) and a Zoho Mail Lite inbox (~$1.25/mo). Set up SPF/DKIM/DMARC and warm the inbox up for 2 weeks.
2. Copy `income-engine/.env.example` to `.env` and fill in your name, mailing address, email and SMTP login.
3. Approve drafts in Business HQ, then run `send_emails.py` (dry run first, then `--send`).

## When someone says yes

The offer is **free setup + a free first 30 days, then $197/month** (Sales kit, section 0). Collect the onboarding answers (section 6), including their average job value. Then upgrade Twilio (~$20), register their business for texting, host the app (~$5/mo), and fill in `lead-responder/clients.json`. That's about $50 out of pocket before the first payment.

Around day 25 of their free month, run `python lead-responder/report.py --business +1THEIRNUMBER --start <go-live date>` and send them the report. That's when you ask for the $197/month (Sales kit, section 9).
