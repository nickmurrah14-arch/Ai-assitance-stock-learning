# Income Engine Playbook

Research date: September 2026. Goal: get paying customers fast, with as much of the work automated as possible, starting with no audience and a very small budget.

## The short version

1. **Nothing legitimate is 100% passive at the start.** Anything sold as "fully passive AI income" is usually selling you a course. What *can* be automated is the hard, boring part: **finding customers, researching them, writing to them, and following up.** You (plus Claude Code) handle the ~20% that closes deals and delivers the work. Once you have clients on monthly plans, the income becomes mostly passive.
2. **Best odds right now:** sell a simple **AI "never miss a lead" setup to local service businesses** (plumbers, HVAC, roofers, dentists, med spas, law firms, auto shops). Find them automatically with this repo's pipeline. Charge a setup fee plus a monthly fee.
3. **Run a second channel at the same time:** list the same skills as a gig on **Upwork/Fiverr**. There, buyers come to you, which is the fastest path to the first dollar.
4. **Skip:** trading bots, faceless AI YouTube channels, and dropshipping. The data on each is below.

---

## 1. About the "only ~1% of people use AI for code" stat

It's roughly right for the whole population, but it's the wrong number to act on:

- Among **developers**, AI use is nearly universal: 84–90% use AI tools, and about half use them daily ([SQ Magazine](https://sqmagazine.co.uk/ai-coding-statistics/), [Panto](https://www.getpanto.ai/blog/ai-coding-tools-adoption-statistics-by-country)). GitHub Copilot alone reported 50M users in July 2026, about 0.6% of the world's population.
- So "~1% of people code with AI" is about right globally. But you won't win by being one of the few people who code with AI. The developers already do.

**The number that matters: most small businesses still don't use AI.**

- US Census Bureau (Dec 2025–May 2026): only **17–20% of US businesses** use AI at all. For firms with **4 or fewer employees, it's under 20%**. Firms with 250+ employees are at 37% ([Census](https://www.census.gov/library/stories/2026/05/ai-use-businesses.html)).
- These businesses have real, expensive problems that AI fixes cheaply, and they don't have anyone to set it up. That gap is your market.

## 2. What each option actually looks like (the data)

| Path | Time to first $ | Odds | Automatable | Verdict |
|---|---|---|---|---|
| **AI lead-response setup for local businesses** (this repo) | 2–6 weeks | Good if you do the outreach volume | Prospecting ~90%, delivery ~70% | **Do this** |
| **Upwork/Fiverr automation gigs** (n8n, Zapier, AI agents) | 1–4 weeks | Good, but competitive | Low, since it's client work | **Do in parallel** |
| Micro-SaaS product | 3–6+ months; early revenue is often $50–500/mo ([ideaproof](https://ideaproof.io/lists/micro-saas-ideas)) | Low without an audience | High once it's built | Later: turn the service into a product |
| Trading / trading bots | Instant, but negative on average | Only 1–4% of day traders stay profitable; 70–80%+ of retail bots lose money ([Vetted Prop Firms](https://vettedpropfirms.com/what-percentage-of-day-traders-lose-money/), [Tradewink](https://www.tradewink.com/learn/are-trading-bots-profitable)) | 100% | **Avoid as an income plan** |
| Faceless AI YouTube | 4–6+ months to monetize | YouTube cut monetization for mass-produced "AI slop" on Jul 16, 2026 ([source](https://www.facelessyoutubechannelidea.com/p/the-harsh-truth-about-youtube-automation-no-one-talks-about-2026-update)) | High | **Avoid** |

Why a service beats a product for speed: AI made building software cheap, so **distribution is the whole game** ([ideaproof](https://ideaproof.io/lists/micro-saas-ideas)). A service sells on a single conversation. A product needs traffic and trust you don't have yet.

## 3. The offer: "Never miss a lead"

**Why this offer:**

- The average small business misses **~62% of incoming calls**, and **85% of those callers never call back** ([Magicline](https://www.magicline.ai/blog/ai-receptionist-statistics-2026)). 30–40% of calls to home-service businesses come in after hours.
- Leads contacted within 5 minutes convert about **9x** more often than leads contacted after 30 minutes ([Promptmaxxing](https://promptmaxxing.ai/guides/speed-to-lead-statistics)).
- A part-time receptionist costs $1,500–2,500/mo. The tools to automate this cost $30–100/mo. You sit in the middle.
- It's easy to explain in one sentence, and the ROI is obvious: one saved job ($300–$10,000 for a roof, HVAC unit, or implant) pays for a year.

**What you deliver** (Claude Code can help build each piece):

1. **Missed-call text-back:** when a call isn't answered, the caller gets a text within seconds: "Sorry we missed you, what can we help with?"
2. **24/7 AI reply** on the website chat and the texts, which answers FAQs, collects job details, and books an appointment.
3. **Instant alert** to the owner with a summary of every lead.
4. Optional upsell: **automatic review requests** after each job. The audit flags businesses with fewer than 25 Google reviews.

**How to build it:**

- Fastest: GoHighLevel (~$97/mo, which covers unlimited clients). Missed-call text-back, chat widget, and review requests are built in, and you can white-label it.
- Cheapest and most flexible: Twilio plus n8n (self-hosted) plus the Claude API.
- US business texting requires **A2P 10DLC registration** for each client's number. Budget 1–2 weeks for approval.

**Pricing (start here, raise it after 5 clients):**

- Setup fee: **$300–$750**. This covers your tool costs and filters out non-serious buyers.
- Monthly: **$150–$300** for hosting, monitoring, and tweaks.
- Guarantee: "If it doesn't recover at least one lead in the first 30 days, I refund the setup fee." This makes saying yes easy.

**Example math, not a promise:** 5 clients = $1,500–$3,750 upfront plus $750–$1,500/mo recurring. 20 clients = $3,000–$6,000/mo, mostly passive.

## 4. The automated prospecting machine (this repo)

```
find_leads.py  ->  audit_sites.py  ->  write_emails.py  ->  (you approve)  ->  send_emails.py  ->  send_emails.py --followups
Google Places      site + reviews      Claude writes a       2 min/day           30/day per inbox     same-thread bump
free tier          audit, emails       specific email                                                 after 4 days
```

- **Find:** the Google Places API gives name, phone, website, rating, and review count. The free tier is 5,000 searches/month at 20 results each ([Google](https://developers.google.com/maps/documentation/places/web-service/usage-and-billing)).
- **Audit:** checks for online booking, chat or after-hours reply, a contact form, mobile setup, HTTPS, an outdated footer, load time, and review count. It also finds a contact email.
- **Write:** Claude turns the findings into a 60–110 word email built on a *specific, true* observation. Personalized, signal-based emails get 15–25%+ reply rates, versus 3–5% for generic templates ([Salesmotion](https://salesmotion.io/blog/cold-outreach-best-practices), [Sopro](https://sopro.io/resources/blog/cold-outreach-statistics/)).
- **Send + follow up:** slow, human-paced sending. **70–80% of replies come after the first email**, so the follow-up matters ([SalesCaptain](https://www.salescaptain.io/outreach-guide/how-to-do-cold-outreach-for-local-businesses)).
- **Benchmark:** 200–400 personalized emails to a tight niche → 5–15 calls → 1–5 clients at a 30–40% close rate ([Systemify](https://www.systemifyautomation.com/blog/why-cold-outreach-is-the-most-important-growth-channel-for-agencies-serving-local-businesses)).

Setup commands are in [README.md](README.md).

## 5. Rules that keep you legal and out of spam (don't skip)

**Email (CAN-SPAM + Gmail/Yahoo/Microsoft rules):**

- Cold email to businesses is legal in the US if you include a **real postal address** (a PO box or virtual mailbox is fine), an **honest subject line**, and a **working opt-out that you honor**. The pipeline adds the footer and a List-Unsubscribe header ([compliance checklist](https://litemail.ai/blog/cold-email-compliance-checklist-2026)).
- **Never send from your main domain.** Buy 1–3 lookalike domains (e.g. `tryacme.com`) with a Google Workspace inbox on each. Set up **SPF, DKIM, and DMARC**. Mail without them is now rejected outright ([Instantly](https://instantly.ai/blog/how-to-achieve-90-cold-email-deliverability-in-2025/), [Mailpool](https://mailpool.ai/blog/googles-2026-bulk-sender-rules-what-cold-email-teams-must-change-without-killing-volume)).
- **Warm up** each inbox for about 2 weeks before sending, then stay around **30/day per inbox**. Keep spam complaints under 0.3% and bounces under 2%.
- Anyone who replies "stop" goes into `data/suppression.txt`, and the pipeline never contacts them again.
- Outside the US, rules are stricter (GDPR in the EU/UK, CASL in Canada). Stick to US businesses to start.

**Phone and text (TCPA). This is where people get sued:**

- **Do not cold-text or AI-cold-call prospects.** Automated marketing texts and AI-voice calls to cell phones need prior written consent. Fines are **$500–$1,500 per message**, with no cap ([Retell](https://www.retellai.com/blog/tcpa-compliance-playbook-voice-ai-outbound), [Revmo](https://revmo.ai/blog/tcpa-compliance-guide-ai)). Use email for outreach and make phone calls yourself.
- The missed-call text-back you sell is a reply to someone who just called the business, which is generally treated differently. Still include "Reply STOP to opt out" and honor it. Have a lawyer glance at your client setup once you have a few clients. This playbook is not legal advice.

## 6. First 30 days

**Week 1: set up (about 5–8 hours total)**

- [ ] Pick **one niche + one metro area** (e.g. HVAC in Phoenix). Tight targeting beats volume.
- [ ] Buy 2 sending domains + Google Workspace inboxes, set up SPF/DKIM/DMARC, and start warmup.
- [ ] Get API keys: Google Places, Anthropic. Fill in `.env`.
- [ ] Build a **demo** of the missed-call text-back on your own number (GoHighLevel trial or Twilio). Record a 60-second screen video. It's your best sales asset.
- [ ] Post an Upwork profile + Fiverr gig: "AI missed-call text-back & lead follow-up setup" and "n8n / Zapier AI automation."
- [ ] Get a booking link (Calendly free tier).

**Week 2: fill the pipeline while domains warm up**

- [ ] `find_leads.py` for 5–10 queries in your niche → 300–600 leads.
- [ ] `audit_sites.py` → `write_emails.py`, then review the drafts. Tighten the `OFFER` and the system prompt until the drafts read like you.
- [ ] Apply to 5 Upwork jobs a day with a short, specific proposal.

**Weeks 3–4: send and sell**

- [ ] 30–60 emails/day plus automatic follow-ups. Reply to every response within an hour. Speed-to-lead applies to you too.
- [ ] On calls, show the demo video and their own audit findings, then offer the refund guarantee.
- [ ] Track results: sent → replies → calls → clients. If reply rate is under 3% after 300 sends, change the niche or the offer, not the volume.

**Month 2 and beyond: make it passive**

- Turn each client setup into a template so onboarding a new client takes under an hour.
- Schedule the pipeline to run daily with cron or a Claude Code routine. Your daily job becomes approving drafts (5 min) and taking calls.
- After 10+ clients, consider turning the setup into a self-serve micro-SaaS for the same niche. By then you'll have the audience and testimonials a product needs.

## Sources

- AI coding adoption: [SQ Magazine](https://sqmagazine.co.uk/ai-coding-statistics/), [Panto](https://www.getpanto.ai/blog/ai-coding-tools-adoption-statistics-by-country), [Second Talent](https://www.secondtalent.com/resources/ai-coding-assistant-statistics/)
- Business AI adoption: [US Census BTOS, May 2026](https://www.census.gov/library/stories/2026/05/ai-use-businesses.html), [Ramp AI Index](https://ramp.com/data/ai-index-may-2026)
- Missed calls / speed to lead: [Magicline](https://www.magicline.ai/blog/ai-receptionist-statistics-2026), [Promptmaxxing](https://promptmaxxing.ai/guides/speed-to-lead-statistics), [Joist](https://www.joist.com/workshop/technology/ai-receptionist-missed-calls-into-leads/)
- Cold outreach benchmarks: [Salesmotion](https://salesmotion.io/blog/cold-outreach-best-practices), [Sopro](https://sopro.io/resources/blog/cold-outreach-statistics/), [SalesCaptain](https://www.salescaptain.io/outreach-guide/how-to-do-cold-outreach-for-local-businesses), [Systemify](https://www.systemifyautomation.com/blog/why-cold-outreach-is-the-most-important-growth-channel-for-agencies-serving-local-businesses)
- Deliverability & law: [Instantly](https://instantly.ai/blog/how-to-achieve-90-cold-email-deliverability-in-2025/), [Mailpool](https://mailpool.ai/blog/googles-2026-bulk-sender-rules-what-cold-email-teams-must-change-without-killing-volume), [LiteMail](https://litemail.ai/blog/cold-email-compliance-checklist-2026), [Retell (TCPA)](https://www.retellai.com/blog/tcpa-compliance-playbook-voice-ai-outbound)
- Freelance demand: [Upwork n8n experts](https://www.upwork.com/hire/n8n-experts/), [Upwork AI automation engineers](https://www.upwork.com/hire/ai-automation-engineers/)
- Micro-SaaS timelines: [ideaproof](https://ideaproof.io/lists/micro-saas-ideas), [Infinity Sky AI](https://infinitysky.ai/blog/launch-micro-saas-ai-big-revenue)
- Trading odds: [Vetted Prop Firms](https://vettedpropfirms.com/what-percentage-of-day-traders-lose-money/), [Tradewink](https://www.tradewink.com/learn/are-trading-bots-profitable)
- Agency model criticism (worth reading): [LinkedIn – "why this business model is broken"](https://www.linkedin.com/pulse/what-i-learned-building-ai-automation-agency-why-nadia-privalikhina-atk0f)
- Open-source tools: [omkarcloud/google-maps-scraper](https://github.com/omkarcloud/google-maps-scraper) (alternative lead source), [warmbly/warmbly](https://github.com/warmbly/warmbly) (open-source outreach + warmup)
