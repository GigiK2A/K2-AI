from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable

GRAPH = "https://graph.facebook.com"

Fetcher = Callable[[str], dict[str, Any]]


def _urllib_fetch(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=20) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Meta manda il VERO errore (es. token invalidato) nel body anche sui 4xx:
        # senza leggerlo qui, resterebbe un generico "HTTP 400 Bad Request".
        try:
            return json.loads(exc.read().decode("utf-8"))
        except Exception:
            raise


class InstagramError(RuntimeError):
    pass


def _friendly_ig_error(err: Any) -> str:
    """Traduce l'errore Graph API in un messaggio chiaro per l'agente/owner.
    In particolare il token scaduto/invalidato (code 190) — la causa più comune."""
    if not isinstance(err, dict):
        return str(err)
    code = err.get("code")
    msg = str(err.get("message") or "")
    if code == 190 or "access token" in msg.lower() or "session" in msg.lower():
        return ("Token Instagram scaduto o invalidato dalla Meta API: va RINNOVATO "
                "(variabile AIOS_IG_TOKEN sul servizio k2-ai-board). "
                f"Dettaglio Meta: {msg}")
    return msg or str(err)


class InstagramClient:
    def __init__(self, token: str, ig_user_id: str = "17841429842127461",
                 version: str = "v21.0", fetch: Fetcher = _urllib_fetch) -> None:
        self._token = token
        self._uid = ig_user_id
        self._version = version
        self._fetch = fetch

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        q = dict(params)
        q["access_token"] = self._token
        url = f"{GRAPH}/{self._version}/{path}?{urllib.parse.urlencode(q)}"
        data = self._fetch(url)
        if isinstance(data, dict) and "error" in data:
            raise InstagramError(_friendly_ig_error(data["error"]))
        return data

    def account(self) -> dict[str, Any]:
        return self._get(self._uid,
                         {"fields": "username,followers_count,media_count"})

    def recent_media(self, limit: int = 10) -> list[dict[str, Any]]:
        data = self._get(f"{self._uid}/media", {
            "fields": "id,caption,media_type,permalink,timestamp,"
                      "like_count,comments_count",
            "limit": str(limit),
        })
        return data.get("data", [])

    def comments(self, media_id: str, limit: int = 25) -> list[dict[str, Any]]:
        """Testo dei commenti sotto un post (+ risposte). comments_count dà solo il numero,
        questo dà il CONTENUTO effettivo, per poter rispondere."""
        data = self._get(f"{media_id}/comments", {
            "fields": "id,text,username,timestamp,like_count,"
                      "replies{id,text,username,timestamp}",
            "limit": str(limit),
        })
        return data.get("data", [])

    def latest_comments(self, media_limit: int = 10,
                        per_post: int = 25) -> list[dict[str, Any]]:
        """Scorre i post recenti CHE HANNO commenti e ne legge il testo. Ritorna una lista
        piatta {post_id, post_caption, permalink, comment_id, text, username, timestamp,
        replies}. Così l'agente vede subito 'cosa dicono i commenti' senza id manuali."""
        out: list[dict[str, Any]] = []
        for m in self.recent_media(limit=media_limit):
            if not (m.get("comments_count") or 0):
                continue
            cap = (m.get("caption") or "")[:80]
            try:
                for c in self.comments(m["id"], limit=per_post):
                    out.append({
                        "post_id": m.get("id"), "post_caption": cap,
                        "permalink": m.get("permalink"),
                        "comment_id": c.get("id"), "text": c.get("text"),
                        "username": c.get("username"), "timestamp": c.get("timestamp"),
                        "like_count": c.get("like_count"),
                        "replies": [r.get("text") for r in
                                    ((c.get("replies") or {}).get("data") or [])],
                    })
            except InstagramError:
                continue
        return out

    def business_discovery(self, username: str, media_limit: int = 6) -> dict[str, Any]:
        fields = (
            f"business_discovery.username({username})"
            "{username,followers_count,media_count,"
            f"media.limit({media_limit})"
            "{caption,like_count,comments_count,timestamp,media_type,permalink}}"
        )
        data = self._get(self._uid, {"fields": fields})
        return data.get("business_discovery", {})

    def account_insights(self,
                         metrics=("reach", "accounts_engaged",
                                  "total_interactions", "profile_views"),
                         period: str = "day") -> dict[str, Any]:
        data = self._get(f"{self._uid}/insights", {
            "metric": ",".join(metrics),
            "period": period,
            "metric_type": "total_value",
        })
        out = {}
        for m in data.get("data", []):
            tv = m.get("total_value") or {}
            out[m.get("name")] = tv.get("value")
        return out
