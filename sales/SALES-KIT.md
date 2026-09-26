# Sales Kit: Missed Call Rescue (HVAC & plumbing, Deltona area)

Everything you need to talk to owners, by phone, in person, or on freelance sites. Replace "Missed Call Rescue" if you pick a different name.

---

## 0. The offer (founding offer, first 5 businesses)

> **"Try it free for 30 days. If it catches you work, keep it for $197 a month. If it doesn't, you owe nothing."**

- **Free setup.** You cover the setup and the carrier texting registration (~$25–40 per business, see section 9).
- **First 30 days free**, starting the day texting goes live, so the 1–2 week carrier wait doesn't eat into it. No card, no contract.
- **Report around day 25:** every missed call it caught and every lead it sent them (`python lead-responder/report.py`).
- **Then $197/month**, locked in for as long as they stay. Cancel anytime with one text.
- **Slow-month guarantee:** any month it sends them fewer than 2 leads, they don't pay for that month.
- **What you ask in return:** 20 minutes to set it up, one call-forwarding setting, 10 minutes at the end to look at the results together, and an honest review if they like it.

Why it works: saying yes to the trial costs them nothing and takes 20 minutes. Saying yes to $197 happens *after* they've watched the lead texts arrive for a month, with a report putting a dollar figure on it. Turning it off means going back to losing those callers.

**Why not a profit share?** You can't see their invoices, so you'd be billing on numbers they report, which is awkward and easy to under-report. Leads are something the system counts itself, and the owner gets a text for every one, so both sides can see the same number.

## 1. The 20-second pitch

> "Hi, I'm [name], I'm local here in Deltona. I set up a system for HVAC and plumbing companies so when you miss a call, because you're on a job or it's after hours, the customer gets a text back within seconds. It gets their name, address and what's wrong, then texts you the lead. Most people who hit voicemail just call the next company, so this keeps them with you. Could I show you a 10-minute demo?"

## 2. Phone call script (calling the business)

**Best times:** 7–8am before they head out, 11:30–1 around lunch, or 4:30–6pm. Avoid Monday mornings and the hottest summer afternoons (their busiest times).

1. **Opener:** "Hi, is this the owner? ... Great. I'm [name], I'm in Deltona. I'll be quick. Do you ever miss calls while you're out on jobs?"
2. **If yes (almost always):** "What usually happens to those? Voicemail?" *(Let them talk. They're telling you the pain.)*
3. **Bridge:** "Most people who hit voicemail don't leave one, they just call the next company. What I do is make sure every missed call gets a text back in seconds. It collects the job details and sends them to you, even at 11pm."
4. **Ask:** "Can I show you in 10 minutes? I can come by, or do it on a video call. Which is easier, [day] or [day]?"
5. **If they're busy:** "Totally get it. Can I text you a 30-second example so you can see it when you have a minute?" *(Only text them after they say yes. That's consent.)*

**If you get a receptionist:** "I'm local, and I help HVAC companies catch the calls that come in when the office is closed or the lines are busy. Who handles decisions on the phones and marketing?" Get the owner's name and the best time to reach them.

## 3. Walk-in / in-person demo (10 minutes)

1. Ask: "Roughly how many calls a week do you think you miss? What's an average repair ticket worth?" Do the math out loud: *"If even 2 of those a month would've booked at $300–400, that's $600–800 a month walking away."*
2. Show the demo: `python lead-responder/simulate.py` on a laptop (play the customer: "my AC is blowing warm air"), or the example conversation on the website on your phone.
3. Show the emergency example ("I smell gas"). Owners care a lot that it handles this safely.
4. Show their own audit finding if you have one ("I noticed your site doesn't have a way to request service online...").
5. **Close:** "Here's the deal: setup is free and the first 30 days are free. No card. At the end I show you every call it caught. If it's making you money, it's $197 a month. If not, I turn it off. Want me to get you started this week?"

## 4. Objections

| They say | You say |
|---|---|
| "We answer all our calls." | "That's great, most don't. What about after 6pm and on weekends? And when you're on a call and a second one comes in? This only kicks in when a call isn't picked up, so it costs you nothing when you do answer." |
| "Too expensive." | "The first month is free, so you'll see exactly what it catches before you spend a dollar. After that, one saved AC repair a month pays for it, and any month it sends you fewer than 2 leads is free." |
| "I don't want another monthly bill." | "Fair. That's why you don't pay anything the first month. If the report doesn't show it paying for itself, don't keep it." |
| "What's the catch?" | "No catch. I'm new, so I'd rather prove it works than ask you to trust me. All I ask is 20 minutes to set it up and 10 minutes at the end to look at the results." |
| "I don't want a robot talking to my customers." | "Fair. It doesn't pretend to be a person, and it doesn't quote prices or promise times. It just says 'sorry we missed you,' gets the details, and hands them to you. You still make the call." |
| "We already have an answering service." | "How much do you pay for it? This is usually cheaper, it replies in seconds by text, which a lot of people prefer, and you get the details in writing." |
| "Who else uses this?" / "Do you have references?" | "Honestly, you'd be one of my first clients. That's why the first month is free: you see real results before you pay anything." |
| "Let me think about it." | "Of course. What's the part you're unsure about?" *(Then answer that.)* "Can I follow up Thursday?" |
| "Send me an email." | "Happy to. What's the best address? I'll include a short video of it working." |
| "What if it says something wrong?" | "It only uses facts you approve: services, hours, area, and your emergency policy. We test it together before it goes live. You get a text summary of every lead, and I can send you the full conversation for any of them." |

## 5. Follow-up texts and emails (only to people who said yes to being contacted)

**Same day after a call/visit:**
> "Thanks for the time today, [name]. Here's the example I mentioned: [website link]. Happy to get you set up whenever you're ready. [your name]"

**3 days later:**
> "Hi [name], [your name] here, following up on the missed-call texting. Any questions I can answer? Setup's free and so is the first month. It goes live once the carrier approves your texting registration, usually within 1–2 weeks, and your free 30 days start then."

## 6. Onboarding questions (after they say yes)

Collect these for `lead-responder/clients.json`:
1. Business name as customers know it
2. Owner's cell for lead alerts (and a second person, if any)
3. Service area (cities, zip codes, or a radius)
4. Hours, and whether they do 24/7 emergencies (and the after-hours fee policy)
5. Services offered (and what they *don't* do)
6. How fast they call leads back (business hours / after hours)
7. Booking link, if they have one
8. Their phone carrier (for the call-forwarding code)
9. Anything customers always ask (financing, free estimates, brands serviced)
10. Legal business name, EIN or sole-prop info, and address, for the texting registration
11. Their average job value (e.g. $350). It goes in `clients.json` as `"avg_job_value"` so their report shows what the leads were worth.

Write down the trial start date (the day texting goes live) so you know when day 25 is.

---

## 7. Fiverr gig

**Title:** I will set up an AI missed call text back system for your service business

**Category:** Programming & Tech → AI Services → AI Agents (or Chatbots)

**Description:**
> Losing jobs to missed calls? When you can't pick up, most callers don't leave a voicemail. They call your competitor.
>
> I'll set up a system that **texts back every missed call within seconds**, has a friendly AI assistant collect the customer's name, address, problem and availability, and **sends you the lead by text**. It's built for HVAC, plumbing, electrical, roofing and other home-service businesses.
>
> **What you get:**
> - Missed-call text-back on your existing number (no number change)
> - An AI texting assistant trained only on your business facts (services, hours, area)
> - Emergency handling (gas smell → tells the customer to call 911 and alerts you right away)
> - Opt-out handling and business-texting registration guidance
> - Testing with you before launch
>
> **Why me:** I build these systems myself (Python, Twilio, Claude AI), so you get something tailored to your business, not a template.
>
> Message me before ordering and tell me your business type and phone carrier.

**Packages:**
- **Basic ($150):** missed-call text-back with your custom message, no AI (fixed replies)
- **Standard ($350):** + AI texting assistant that collects job details, plus owner lead alerts
- **Premium ($600):** + emergency handling, 2 weeks of tuning, and help with texting registration

*(Hosting and texting costs are billed separately monthly, or offered as a $97–197/mo maintenance plan.)*

**Tags:** missed call text back, ai chatbot, twilio, lead generation, hvac marketing

## 8. Upwork profile

**Title:** AI Automation Developer | Missed-Call Text-Back, SMS Chatbots, Twilio + Claude/OpenAI | Python

**Overview:**
> I build AI automations that bring in revenue for service businesses. My main system texts back every missed call within seconds, uses an AI assistant to collect the job details, and sends the lead to the owner. It's built for HVAC, plumbing and home-service companies, where a missed call is a lost job.
>
> What I can build for you:
> - Missed-call text-back and AI SMS assistants (Twilio)
> - Lead intake and qualification bots that route to your CRM or phone
> - Website audits and automated, personalized outreach pipelines
> - Python scripts, integrations, and API automations (Claude, OpenAI, Twilio, Google APIs)
>
> I write clean, tested code, explain things in plain English, and I'm quick to respond. Tell me the process that's eating your time and I'll tell you honestly whether automation will pay off.

**Skills:** Python, Twilio, AI Chatbot Development, API Integration, Automation, Lead Generation, Flask, Anthropic Claude, OpenAI API

**Portfolio item:** "Missed-call text-back + AI SMS assistant for HVAC/plumbing." Use screenshots of the website demo, `simulate.py` output, and the architecture line from `lead-responder/README.md`.

### Upwork proposal template (use your 10 free Connects on the best-fit jobs)
> Hi [name]. You mentioned [specific detail from their post]. I've built exactly this kind of system: [one sentence on the most relevant thing you've built].
>
> For your project I'd [2–3 concrete steps].
>
> Quick question so I scope it right: [one smart question about their setup].
>
> I can start [day]. Happy to hop on a short call.
> [your name]

**Which jobs to apply to:** search "missed call text back", "Twilio SMS", "AI receptionist", "lead follow up automation", "GoHighLevel automation", and "n8n". Pick posts less than 24 hours old, with fewer than 10 proposals, where the client's payment method is verified.

---

## 9. Turning the free month into $197/month

| When | What you do |
|---|---|
| **Go-live day** | Text them: "You're live! Call your business line from another phone and don't answer, to see it work. Your free 30 days start today." |
| **Every lead** | Nothing. They get a text for every lead automatically. Each one reminds them it's working. |
| **Day 7** | Short check-in text: "First week: it caught X missed calls and sent you Y leads. Anything you want the texts to say differently?" (Run `report.py` with `--start` set to the go-live date.) |
| **Day 25** | Run `python lead-responder/report.py --business +1THEIRNUMBER --start <go-live date>`, send them the report, and book the 10-minute look together. |
| **The ask** | "Here's what it caught this month: X calls, Y leads. At your ~$Z average job, even half of those is $W. Want to keep it for $197 a month?" Send a payment link (Stripe or Square) when they say yes. |
| **If no** | Thank them, turn it off, and have them switch off call forwarding. Ask what would have made it worth it. |
| **Monthly after that** | Send the report with each invoice. Any month under 2 leads, don't bill it. |

**What each free trial costs you:** about $25–40 once (their carrier texting registration and phone number), plus about $5–10 a month while it runs (number, texts, AI). Five trials that all said no would cost about $150–200 in total, so pick owners who told you they miss calls, and cap it at 5 founding spots. Each one that converts brings in $197 a month, about $185 of it profit.

**Referral bonus (optional):** "If you send me another business owner who signs up, your next month is free."
