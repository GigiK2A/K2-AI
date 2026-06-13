from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any, Callable

HTTP = Callable[..., Any]


def _urllib_http(*, method: str, url: str, headers: dict[str, str],
                 body: str | None) -> Any:
    data = body.encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=20) as resp:  # noqa: S310
        raw = resp.read().decode("utf-8")
    return json.loads(raw) if raw else []


class SupabaseRESTError(RuntimeError):
    pass


class SupabaseREST:
    def __init__(self, *, url: str, service_key: str, fetch: HTTP = _urllib_http) -> None:
        self._base = url.rstrip("/") + "/rest/v1"
        self._key = service_key
        self._fetch = fetch

    def _headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        h = {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }
        if extra:
            h.update(extra)
        return h

    def select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        qs = urllib.parse.urlencode(params, safe="*")
        url = f"{self._base}/{table}?{qs}"
        return self._fetch(method="GET", url=url, headers=self._headers(), body=None)

    def insert(self, table: str, row: dict[str, Any]) -> list[dict[str, Any]]:
        url = f"{self._base}/{table}"
        return self._fetch(method="POST", url=url,
                           headers=self._headers({"Prefer": "return=representation"}),
                           body=json.dumps(row))

    def upsert(self, table: str, row: dict[str, Any], *, on_conflict: str) -> list[dict[str, Any]]:
        url = f"{self._base}/{table}?on_conflict={urllib.parse.quote(on_conflict, safe='')}"
        return self._fetch(method="POST", url=url,
                           headers=self._headers(
                               {"Prefer": "return=representation,resolution=merge-duplicates"}),
                           body=json.dumps(row))

    def update(self, table: str, filters: dict[str, str],
               patch: dict[str, Any]) -> list[dict[str, Any]]:
        qs = urllib.parse.urlencode(filters, safe="*")
        url = f"{self._base}/{table}?{qs}"
        return self._fetch(method="PATCH", url=url,
                           headers=self._headers({"Prefer": "return=representation"}),
                           body=json.dumps(patch))

    def delete(self, table: str, filters: dict[str, str]) -> list[dict[str, Any]]:
        # I filtri sono OBBLIGATORI (il chiamante li garantisce): senza, PostgREST
        # rifiuta comunque una DELETE non filtrata, ma non ci affidiamo a quello.
        qs = urllib.parse.urlencode(filters, safe="*")
        url = f"{self._base}/{table}?{qs}"
        return self._fetch(method="DELETE", url=url,
                           headers=self._headers({"Prefer": "return=representation"}),
                           body=None)
