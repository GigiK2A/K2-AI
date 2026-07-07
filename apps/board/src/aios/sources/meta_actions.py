"""Azioni SCRITTURA su Meta (Instagram + Ads) — eseguite SOLO su conferma umana (L1).

Coperte:
- pubblicare un post Instagram (Content Publishing API, serve un'immagine a URL pubblico)
- rispondere a un commento Instagram
- creare una campagna ads (Marketing API) — SEMPRE in stato PAUSED: non spende finché
  non la attivi tu in Meta Ads Manager

Credenziali da env: AIOS_IG_TOKEN (Page token con instagram_content_publish/ads_management),
AIOS_IG_USER_ID, META_AD_ACCOUNT_ID (act_XXXX). Le chiamate passano dall'attuatore, quindi
girano solo dopo che l'owner ha approvato la proposta.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

GRAPH = "https://graph.facebook.com"
VER = "v21.0"

# obiettivo campagna: sinonimi italiani → enum Meta (Outcome-Driven Ad Experiences)
_OBJECTIVES = {
    "traffico": "OUTCOME_TRAFFIC", "traffic": "OUTCOME_TRAFFIC",
    "lead": "OUTCOME_LEADS", "leads": "OUTCOME_LEADS", "contatti": "OUTCOME_LEADS",
    "engagement": "OUTCOME_ENGAGEMENT", "interazioni": "OUTCOME_ENGAGEMENT",
    "notorieta": "OUTCOME_AWARENESS", "awareness": "OUTCOME_AWARENESS",
    "vendite": "OUTCOME_SALES", "conversioni": "OUTCOME_SALES", "sales": "OUTCOME_SALES",
}

Poster = Callable[[str, dict, str], dict]


def _http_post(path: str, data: dict, token: str) -> dict[str, Any]:
    body = urllib.parse.urlencode({**data, "access_token": token}).encode("utf-8")
    req = urllib.request.Request(f"{GRAPH}/{VER}/{path}", data=body)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:  # noqa: S310
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            return json.loads(exc.read().decode("utf-8"))
        except Exception:
            return {"error": {"message": f"HTTP {exc.code}"}}


def _err(resp: Any) -> str:
    e = resp.get("error", {}) if isinstance(resp, dict) else {}
    m = str(e.get("message") or e or resp)
    if e.get("code") == 190:
        m = "Token Instagram scaduto/invalidato — rinnovalo (AIOS_IG_TOKEN). " + m
    return m[:300]


# ───────────────────────── Instagram ─────────────────────────

def publish_post(caption: str | None, image_url: str | None, *, token: str,
                 ig_user_id: str, post: Poster = _http_post) -> dict[str, Any]:
    """Pubblica un post IG: crea il contenitore media poi lo pubblica. L'immagine deve
    essere raggiungibile a un URL PUBBLICO (Meta la preleva)."""
    if not image_url:
        return {"ok": False, "errore": "serve un'immagine a URL pubblico (image_url)"}
    c = post(f"{ig_user_id}/media", {"image_url": image_url, "caption": caption or ""}, token)
    if "error" in c:
        return {"ok": False, "errore": _err(c)}
    cid = c.get("id")
    p = post(f"{ig_user_id}/media_publish", {"creation_id": cid}, token)
    if "error" in p:
        return {"ok": False, "errore": _err(p), "creation_id": cid}
    return {"ok": True, "post_id": p.get("id"), "creation_id": cid}


def reply_comment(comment_id: str | None, message: str | None, *, token: str,
                  post: Poster = _http_post) -> dict[str, Any]:
    """Risponde a un commento IG."""
    if not comment_id or not message:
        return {"ok": False, "errore": "servono comment_id e message"}
    r = post(f"{comment_id}/replies", {"message": message}, token)
    if "error" in r:
        return {"ok": False, "errore": _err(r)}
    return {"ok": True, "reply_id": r.get("id")}


# ───────────────────────── Ads (Marketing API) ─────────────────────────

def create_ad_campaign(name: str | None, objective: str | None, *, token: str,
                       ad_account_id: str, post: Poster = _http_post) -> dict[str, Any]:
    """Crea una campagna ads SEMPRE in stato PAUSED (non spende). Budget/targeting/creatività
    si completano poi in Ads Manager, o con step successivi. Non attiva mai da sola."""
    if not ad_account_id:
        return {"ok": False, "errore": "META_AD_ACCOUNT_ID non configurato"}
    acct = ad_account_id if ad_account_id.startswith("act_") else f"act_{ad_account_id}"
    obj = _OBJECTIVES.get(str(objective or "").strip().lower(), "OUTCOME_TRAFFIC")
    r = post(f"{acct}/campaigns", {
        "name": name or "Campagna K2-AI",
        "objective": obj,
        "status": "PAUSED",                 # ← chiave di sicurezza: mai attiva da sola
        "special_ad_categories": "[]",
    }, token)
    if "error" in r:
        return {"ok": False, "errore": _err(r)}
    return {"ok": True, "campaign_id": r.get("id"), "obiettivo": obj, "stato": "PAUSED",
            "nota": "Campagna creata IN PAUSA — impostane budget/targeting/creatività e "
                    "ATTIVALA tu in Meta Ads Manager. Non spende finché è in pausa."}


# ───────────────────────── dispatcher (chiamato dall'attuatore) ─────────────────────────

def apply(action: dict[str, Any], post: Poster = _http_post) -> dict[str, Any]:
    """Esegue un'azione Meta (dopo l'approvazione umana). `action` porta 'azione' + campi."""
    token = os.environ.get("AIOS_IG_TOKEN", "")
    ig_user_id = os.environ.get("AIOS_IG_USER_ID", "17841429842127461")
    ad_account = os.environ.get("META_AD_ACCOUNT_ID", "")
    if not token:
        return {"ok": False, "errore": "AIOS_IG_TOKEN non configurato"}
    az = str(action.get("azione") or "").strip().lower()
    if az in ("pubblica_post", "pubblica", "post", "publish"):
        return publish_post(action.get("caption"),
                            action.get("image_url") or action.get("immagine"),
                            token=token, ig_user_id=ig_user_id, post=post)
    if az in ("rispondi_commento", "reply", "commento"):
        return reply_comment(action.get("comment_id"),
                            action.get("message") or action.get("testo"),
                            token=token, post=post)
    if az in ("crea_campagna", "campagna", "ads", "campaign"):
        return create_ad_campaign(action.get("nome") or action.get("name"),
                                 action.get("obiettivo") or action.get("objective"),
                                 token=token, ad_account_id=ad_account, post=post)
    return {"ok": False, "errore": f"azione Meta sconosciuta: {az}"}
