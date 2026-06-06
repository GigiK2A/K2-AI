"""Connettori esterni env-gated (stdlib). Ognuno è un Tool readonly che legge da
un servizio esterno usando credenziali da env; senza credenziali → [] (graceful).
Così la piattaforma è "deploy-ready": l'unica cosa mancante sono le credenziali.

Env var per servizio:
- Stripe   : STRIPE_API_KEY (restricted, read-only)
- Resend   : RESEND_API_KEY
- GSC      : GSC_SERVICE_ACCOUNT_JSON (path o json), GSC_SITE_URL
- PostHog  : POSTHOG_HOST, POSTHOG_PROJECT_ID, POSTHOG_PERSONAL_KEY
- Meta Ads : META_ACCESS_TOKEN, META_AD_ACCOUNT_ID
- Google Ads: GOOGLE_ADS_* (developer token + oauth) — best effort
- IMAP     : IMAP_HOST, IMAP_USER, IMAP_PASSWORD (IMAP_PORT opz.)
- GCalendar: GOOGLE_SA_JSON (path o json), GCAL_CALENDAR_ID
- Competitor web: COMPETITOR_URLS (csv di url, nessuna credenziale)
"""
from __future__ import annotations

import base64
import os
import urllib.parse
import urllib.request

from aios.tools import Tool
from aios.sources.ext_common import (env, get_json, post_json, safe,
                                     google_sa_token, load_sa)


def _ro(name: str, fn) -> Tool:
    return Tool(name=name, action_type=None, readonly=True, run=lambda **_: safe(fn))


# ---------------------------------------------------------------- Stripe
def _stripe_auth() -> dict:
    key = os.environ["STRIPE_API_KEY"]
    tok = base64.b64encode(f"{key}:".encode()).decode()
    return {"Authorization": f"Basic {tok}"}


def _stripe_ricavi():
    if not env("STRIPE_API_KEY"):
        return []
    out = get_json("https://api.stripe.com/v1/charges?limit=100", headers=_stripe_auth())
    return [{"amount_eur": round((c.get("amount") or 0) / 100, 2), "currency": c.get("currency"),
             "created": c.get("created"), "description": c.get("description")}
            for c in out.get("data", []) if c.get("status") == "succeeded"]


def _stripe_saldo():
    if not env("STRIPE_API_KEY"):
        return []
    out = get_json("https://api.stripe.com/v1/balance", headers=_stripe_auth())
    rows = []
    for kind in ("available", "pending"):
        for b in out.get(kind, []):
            rows.append({"tipo": kind, "amount_eur": round((b.get("amount") or 0) / 100, 2),
                         "currency": b.get("currency")})
    return rows


# ---------------------------------------------------------------- Resend
def _resend_emails():
    if not env("RESEND_API_KEY"):
        return []
    out = get_json("https://api.resend.com/emails?limit=100",
                   headers={"Authorization": f"Bearer {os.environ['RESEND_API_KEY']}"})
    return [{"id": e.get("id"), "to": e.get("to"), "subject": e.get("subject"),
             "last_event": e.get("last_event"), "created_at": e.get("created_at")}
            for e in out.get("data", [])]


# ---------------------------------------------------------------- Google Search Console
def _gsc_ranking():
    if not env("GSC_SERVICE_ACCOUNT_JSON", "GSC_SITE_URL"):
        return []
    sa = load_sa("GSC_SERVICE_ACCOUNT_JSON")
    token = google_sa_token(sa, "https://www.googleapis.com/auth/webmasters.readonly")
    site = urllib.parse.quote(os.environ["GSC_SITE_URL"], safe="")
    import time
    end = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 3 * 86400))
    start = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 33 * 86400))
    body = {"startDate": start, "endDate": end, "dimensions": ["query"], "rowLimit": 50}
    out = post_json(f"https://www.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query",
                    body, headers={"Authorization": f"Bearer {token}"})
    return [{"query": (r.get("keys") or [""])[0], "clicks": r.get("clicks"),
             "impressions": r.get("impressions"), "ctr": r.get("ctr"),
             "position": round(r.get("position", 0), 1)} for r in out.get("rows", [])]


# ---------------------------------------------------------------- PostHog
def _posthog_funnel():
    if not env("POSTHOG_HOST", "POSTHOG_PROJECT_ID", "POSTHOG_PERSONAL_KEY"):
        return []
    host = os.environ["POSTHOG_HOST"].rstrip("/")
    pid = os.environ["POSTHOG_PROJECT_ID"]
    q = ("SELECT event, count() AS cnt FROM events WHERE timestamp > now() - INTERVAL 30 DAY "
         "GROUP BY event ORDER BY cnt DESC LIMIT 50")
    out = post_json(f"{host}/api/projects/{pid}/query/",
                    {"query": {"kind": "HogQLQuery", "query": q}},
                    headers={"Authorization": f"Bearer {os.environ['POSTHOG_PERSONAL_KEY']}"})
    return [{"event": row[0], "count": row[1]} for row in out.get("results", []) if len(row) >= 2]


# ---------------------------------------------------------------- Meta / Google Ads
def _meta_ads():
    if not env("META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"):
        return []
    acct = os.environ["META_AD_ACCOUNT_ID"]
    params = urllib.parse.urlencode({
        "fields": "campaign_name,spend,impressions,clicks,action_values",
        "date_preset": "last_30d", "level": "campaign",
        "access_token": os.environ["META_ACCESS_TOKEN"]})
    out = get_json(f"https://graph.facebook.com/v20.0/act_{acct}/insights?{params}")
    rows = []
    for c in out.get("data", []):
        spend = float(c.get("spend") or 0)
        rev = sum(float(a.get("value") or 0) for a in (c.get("action_values") or [])
                  if "purchase" in (a.get("action_type") or ""))
        rows.append({"campagna": c.get("campaign_name"), "spesa_eur": spend,
                     "impressioni": c.get("impressions"), "click": c.get("clicks"),
                     "roas": round(rev / spend, 2) if spend else None})
    return rows


def _google_ads():
    need = ("GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CLIENT_ID", "GOOGLE_ADS_CLIENT_SECRET",
            "GOOGLE_ADS_REFRESH_TOKEN", "GOOGLE_ADS_CUSTOMER_ID")
    if not env(*need):
        return []
    tok = post_json("https://oauth2.googleapis.com/token", {
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        "grant_type": "refresh_token"}, form=True)
    access = tok["access_token"]
    cid = os.environ["GOOGLE_ADS_CUSTOMER_ID"].replace("-", "")
    headers = {"Authorization": f"Bearer {access}",
               "developer-token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
               "Content-Type": "application/json"}
    login = os.environ.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace("-", "")
    if login:
        headers["login-customer-id"] = login
    q = ("SELECT campaign.name, metrics.cost_micros, metrics.conversions_value "
         "FROM campaign WHERE segments.date DURING LAST_30_DAYS")
    out = post_json(f"https://googleads.googleapis.com/v17/customers/{cid}/googleAds:search",
                    {"query": q}, headers=headers)
    rows = []
    for r in out.get("results", []):
        cost = (r.get("metrics", {}).get("costMicros") or 0)
        rows.append({"campagna": r.get("campaign", {}).get("name"),
                     "spesa_eur": round(int(cost) / 1_000_000, 2),
                     "conversions_value": r.get("metrics", {}).get("conversionsValue")})
    return rows


# ---------------------------------------------------------------- IMAP inbox
def _inbox():
    if not env("IMAP_HOST", "IMAP_USER", "IMAP_PASSWORD"):
        return []
    import email
    import imaplib
    from email.header import decode_header
    host = os.environ["IMAP_HOST"]
    port = int(os.environ.get("IMAP_PORT", "993"))
    rows = []
    with imaplib.IMAP4_SSL(host, port) as M:
        M.login(os.environ["IMAP_USER"], os.environ["IMAP_PASSWORD"])
        M.select("INBOX", readonly=True)
        _, uids = M.search(None, "UNSEEN")
        for uid in uids[0].split()[-20:]:
            _, data = M.fetch(uid, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])
            raw, enc = decode_header(msg.get("Subject", ""))[0]
            subject = raw.decode(enc or "utf-8", "replace") if isinstance(raw, bytes) else raw
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = (part.get_payload(decode=True) or b"").decode("utf-8", "replace")[:400]
                        break
            else:
                body = (msg.get_payload(decode=True) or b"").decode("utf-8", "replace")[:400]
            rows.append({"from": msg.get("From"), "subject": subject,
                         "date": msg.get("Date"), "snippet": body})
    return rows


# ---------------------------------------------------------------- Google Calendar
def _gcal():
    if not env("GOOGLE_SA_JSON"):
        return []
    import time
    sa = load_sa("GOOGLE_SA_JSON")
    token = google_sa_token(sa, "https://www.googleapis.com/auth/calendar.readonly")
    cal = urllib.parse.quote(os.environ.get("GCAL_CALENDAR_ID", "primary"), safe="")
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    fut = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 7 * 86400))
    params = urllib.parse.urlencode({"timeMin": now, "timeMax": fut, "singleEvents": "true",
                                     "orderBy": "startTime", "maxResults": 50})
    out = get_json(f"https://www.googleapis.com/calendar/v3/calendars/{cal}/events?{params}",
                   headers={"Authorization": f"Bearer {token}"})
    return [{"summary": e.get("summary", "(senza titolo)"),
             "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date")),
             "attendees": [a.get("email") for a in e.get("attendees", [])],
             "description": (e.get("description") or "")[:200]}
            for e in out.get("items", [])]


# ---------------------------------------------------------------- PR / brand mentions (free)
def _brand_mentions():
    q = os.environ.get("AIOS_BRAND_NAME")
    if not q:
        return []
    import xml.etree.ElementTree as ET
    url = ("https://news.google.com/rss/search?q=" + urllib.parse.quote(q) +
           "&hl=it&gl=IT&ceid=IT:it")
    req = urllib.request.Request(url, headers={"User-Agent": "K2AI-bot/1.0"})
    with urllib.request.urlopen(req, timeout=12) as r:  # noqa: S310
        raw = r.read()
    root = ET.fromstring(raw)
    rows = []
    for it in root.findall(".//item")[:15]:
        rows.append({"title": (it.findtext("title") or "")[:160],
                     "link": it.findtext("link") or "",
                     "source": (it.find("{*}source").text if it.find("{*}source") is not None else ""),
                     "date": it.findtext("pubDate") or ""})
    return rows


# ---------------------------------------------------------------- Competitor web
def _competitor_web():
    urls = os.environ.get("COMPETITOR_URLS", "")
    if not urls.strip():
        return []
    import re
    rows = []
    for u in [x.strip() for x in urls.split(",") if x.strip()][:8]:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "K2AI-bot/1.0"})
            with urllib.request.urlopen(req, timeout=10) as r:  # noqa: S310
                html = r.read(60000).decode("utf-8", "replace")
            title = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
            desc = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', html, re.I)
            rows.append({"url": u, "title": (title.group(1).strip() if title else "")[:120],
                         "description": (desc.group(1).strip() if desc else "")[:200]})
        except Exception:
            rows.append({"url": u, "title": "(non raggiungibile)", "description": ""})
    return rows


# ---------------------------------------------------------------- factories
def finance_connectors():
    return [_ro("leggi_stripe_ricavi", _stripe_ricavi), _ro("leggi_stripe_saldo", _stripe_saldo)]


def marketing_connectors():
    return [_ro("leggi_email_events", _resend_emails), _ro("leggi_ranking_seo", _gsc_ranking),
            _ro("leggi_funnel_web", _posthog_funnel), _ro("leggi_ads_meta", _meta_ads),
            _ro("leggi_ads_google", _google_ads), _ro("leggi_competitor_web", _competitor_web),
            _ro("leggi_brand_mentions", _brand_mentions)]


def sales_connectors():
    return [_ro("leggi_inbox", _inbox), _ro("leggi_calendario_google", _gcal)]


def all_connectors():
    return finance_connectors() + marketing_connectors() + sales_connectors()


CONNECTOR_ENV = {
    "leggi_stripe_ricavi": ["STRIPE_API_KEY"], "leggi_stripe_saldo": ["STRIPE_API_KEY"],
    "leggi_email_events": ["RESEND_API_KEY"],
    "leggi_ranking_seo": ["GSC_SERVICE_ACCOUNT_JSON", "GSC_SITE_URL"],
    "leggi_funnel_web": ["POSTHOG_HOST", "POSTHOG_PROJECT_ID", "POSTHOG_PERSONAL_KEY"],
    "leggi_ads_meta": ["META_ACCESS_TOKEN", "META_AD_ACCOUNT_ID"],
    "leggi_ads_google": ["GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_REFRESH_TOKEN"],
    "leggi_inbox": ["IMAP_HOST", "IMAP_USER", "IMAP_PASSWORD"],
    "leggi_calendario_google": ["GOOGLE_SA_JSON"],
    "leggi_competitor_web": ["COMPETITOR_URLS"],
    "leggi_brand_mentions": ["AIOS_BRAND_NAME"],
}
