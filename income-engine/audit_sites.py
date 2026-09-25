"""Step 2: audit each lead's website and find a contact email.

The findings become the personal hook in each email ("your site has no way to book
online", "no reply path after hours"), which is what lifts reply rates above
generic templates.

    python audit_sites.py [--pagespeed]
"""
import argparse
import datetime
import re
import time
from urllib.parse import urljoin, urlparse

import requests

import config
from csvio import read_rows, write_rows

UA = "Mozilla/5.0 (compatible; site-audit/1.0)"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
JUNK_EMAIL = re.compile(
    r"(example\.|sentry|wixpress|godaddy|domain\.com|\.png|\.jpg|\.gif|\.webp|@2x|noreply|no-reply)",
    re.I,
)
BOOKING_HINTS = (
    "calendly", "acuityscheduling", "housecallpro", "servicetitan", "jobber",
    "schedulicity", "vagaro", "booksy", "squareup.com/appointments", "setmore",
    "book online", "book now", "schedule online", "request appointment",
)
CHAT_HINTS = (
    "intercom", "drift.com", "tawk.to", "livechat", "crisp.chat", "tidio",
    "hubspot-messages", "podium", "birdeye", "leadconnector", "zendesk",
)


FREE_MAIL = ("gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com", "icloud.com", "live.com",
             "msn.com", "bellsouth.net", "att.net", "comcast.net", "cfl.rr.com", "earthlink.net", "me.com")
PLACEHOLDER_EMAIL = re.compile(r"^(john|jane)@doe\.|^(name|email|your|you|user|test|someone)@", re.I)
LOCAL_AREA_CODES = {"386", "407", "321", "689", "352", "904"}


def find_emails(html: str, site_domain: str) -> list[str]:
    """Emails on the business's own domain, or a free-mail address (small shops often use Gmail).
    Other domains are usually the web designer or a template, so they're skipped."""
    found = []
    for e in EMAIL_RE.findall(html):
        e = e.lower().rstrip(".")
        if JUNK_EMAIL.search(e) or PLACEHOLDER_EMAIL.search(e) or e in found:
            continue
        domain = e.split("@")[1]
        if not (domain == site_domain or domain.endswith("." + site_domain) or domain in FREE_MAIL):
            continue
        found.append(e)
    # Prefer addresses on the business's own domain, then generic role inboxes.
    found.sort(key=lambda e: (not e.endswith(site_domain), e.split("@")[0] not in ("info", "contact", "office", "hello")))
    return found


PHONE_RE = re.compile(r"\(?\b([2-9]\d{2})\)?[\s.-]?([2-9]\d{2})[\s.-]?(\d{4})\b")


def visible_text(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", html)
    return re.sub(r"<[^>]+>", " ", html)


def find_phone(html: str) -> str:
    """First tel: link, else the first US-looking number in the visible text."""
    tel = re.search(r'href=["\']tel:([^"\']+)', html, re.I)
    m = PHONE_RE.search(tel.group(1) if tel else visible_text(html))
    return f"({m.group(1)}) {m.group(2)}-{m.group(3)}" if m else ""


def analyze_html(html: str, url: str) -> dict:
    low = html.lower()
    years = [int(y) for y in re.findall(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?(20\d{2})", low)]
    return {
        "https": url.startswith("https://"),
        "mobile_viewport": 'name="viewport"' in low or "name=viewport" in low,
        "has_form": "<form" in low,
        "online_booking": any(h in low for h in BOOKING_HINTS),
        "chat_widget": any(h in low for h in CHAT_HINTS),
        "copyright_year": max(years) if years else "",
    }


def issues_for(lead: dict, a: dict) -> list[str]:
    """Plain-English problems a business owner would care about."""
    if not lead.get("website"):
        if lead.get("source") == "dbpr":
            return ["couldn't find a website for the business online"]
        return ["no website listed on Google - customers searching can't learn more or contact you online"]
    if a.get("error"):
        return [f"website didn't load when we checked ({a['error']})"]
    out = []
    if not a["online_booking"]:
        out.append("no way to book or request a quote online")
    if not a["chat_widget"]:
        out.append("no instant reply for visitors after hours")
    if not a["has_form"]:
        out.append("no contact form - visitors have to call")
    if not a["mobile_viewport"]:
        out.append("site isn't set up for phones")
    if not a["https"]:
        out.append("site shows 'Not secure' in browsers")
    if a.get("copyright_year") and a["copyright_year"] < datetime.date.today().year - 2:
        out.append(f"footer still says {a['copyright_year']}, so the site looks unmaintained")
    if a.get("load_seconds") and float(a["load_seconds"]) > 4:
        out.append(f"homepage took {a['load_seconds']}s to load")
    if a.get("mobile_score") not in ("", None) and int(a["mobile_score"]) < 50:
        out.append(f"Google PageSpeed mobile score is {a['mobile_score']}/100")
    try:
        if lead.get("reviews") not in ("", None) and int(lead["reviews"]) < 25:
            out.append(f"only {lead['reviews']} Google reviews")
    except ValueError:
        pass
    return out


def fetch(url: str) -> tuple[str, str, float]:
    t = time.time()
    r = requests.get(url, headers={"User-Agent": UA}, timeout=15, allow_redirects=True)
    r.raise_for_status()
    return r.text, r.url, round(time.time() - t, 1)


def pagespeed(url: str) -> str:
    params = {"url": url, "strategy": "mobile", "category": "performance"}
    if config.PAGESPEED_API_KEY:
        params["key"] = config.PAGESPEED_API_KEY
    r = requests.get(
        "https://www.googleapis.com/pagespeedonline/v5/runPagespeed", params=params, timeout=90
    )
    r.raise_for_status()
    score = r.json()["lighthouseResult"]["categories"]["performance"]["score"]
    return str(round(score * 100))


def audit(lead: dict, use_pagespeed: bool) -> dict:
    a: dict = {}
    site = lead.get("website", "")
    if site:
        try:
            html, final_url, secs = fetch(site)
            a = analyze_html(html, final_url)
            a["load_seconds"] = secs
            domain = urlparse(final_url).netloc.removeprefix("www.")
            emails = find_emails(html, domain)
            if not emails:
                for path in ("/contact", "/contact-us", "/about"):
                    try:
                        emails = find_emails(fetch(urljoin(final_url, path))[0], domain)
                    except requests.RequestException:
                        continue
                    if emails:
                        break
            a["email"] = emails[0] if emails else ""
            site_phone = find_phone(html)
            if not lead.get("phone"):
                a["phone"] = site_phone
            if site_phone and site_phone[1:4] not in LOCAL_AREA_CODES:
                a["site_check"] = f"verify: site's phone {site_phone} isn't a Central Florida number - may be a different company"
            if use_pagespeed:
                try:
                    a["mobile_score"] = pagespeed(final_url)
                except (requests.RequestException, KeyError):
                    a["mobile_score"] = ""
        except requests.RequestException as e:
            a = {"error": type(e).__name__, "email": ""}
    issues = issues_for(lead, a)
    return {**lead, **a, "issues": " | ".join(issues), "issue_count": len(issues)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pagespeed", action="store_true", help="also fetch Google PageSpeed mobile score (slow)")
    args = ap.parse_args()
    leads = read_rows(config.LEADS_CSV)
    done = {r["place_id"] for r in read_rows(config.AUDITED_CSV)}
    rows = read_rows(config.AUDITED_CSV)
    todo = [l for l in leads if l["place_id"] not in done]
    for i, lead in enumerate(todo, 1):
        rows.append(audit(lead, args.pagespeed))
        print(f"[{i}/{len(todo)}] {lead['name']}: {rows[-1]['issue_count']} issues, email={rows[-1].get('email') or '-'}")
        write_rows(config.AUDITED_CSV, rows)  # save as we go
    with_email = sum(1 for r in rows if r.get("email"))
    print(f"Audited {len(rows)} leads, {with_email} with an email -> {config.AUDITED_CSV}")
    calls = [
        {k: r.get(k, "") for k in ("name", "phone", "address", "website", "rating", "reviews", "issues")}
        for r in sorted(rows, key=lambda r: int(r.get("issue_count") or 0), reverse=True)
        if not r.get("email") and r.get("phone")
    ]
    write_rows(config.CALL_LIST_CSV, calls)
    print(f"{len(calls)} leads with no email but a phone number -> {config.CALL_LIST_CSV} (call these yourself)")


if __name__ == "__main__":
    main()
