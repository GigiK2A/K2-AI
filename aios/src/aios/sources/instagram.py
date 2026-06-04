from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Callable

GRAPH = "https://graph.facebook.com"

Fetcher = Callable[[str], dict[str, Any]]


def _urllib_fetch(url: str) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=20) as resp:  # noqa: S310
        return json.loads(resp.read().decode("utf-8"))


class InstagramError(RuntimeError):
    pass


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
            raise InstagramError(str(data["error"]))
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
