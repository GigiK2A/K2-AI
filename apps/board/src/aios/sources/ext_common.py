"""Helper condivisi per i connettori esterni (env-gated, stdlib).
Ogni connettore degrada a [] se mancano le credenziali o in caso di errore:
così la piattaforma gira sempre, e "l'unica cosa mancante sono le credenziali".
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request


def env(*names: str) -> bool:
    """True solo se TUTTE le env var indicate sono presenti e non vuote."""
    return all(os.environ.get(n) for n in names)


def get_json(url: str, headers: dict | None = None, timeout: int = 15):
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        raw = r.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def post_json(url: str, payload: dict, headers: dict | None = None,
              timeout: int = 20, form: bool = False):
    if form:
        data = urllib.parse.urlencode(payload).encode()
        h = {"Content-Type": "application/x-www-form-urlencoded"}
    else:
        data = json.dumps(payload).encode()
        h = {"Content-Type": "application/json"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        raw = r.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def safe(fn):
    """Esegue il corpo di un connettore; qualsiasi errore/credenziale mancante → []."""
    try:
        out = fn()
        return out if out is not None else []
    except Exception:
        return []


def google_sa_token(sa: dict, scope: str) -> str:
    """Access token OAuth2 da service account Google (RS256 JWT).
    Usa `cryptography` se presente; se assente solleva → safe() restituirà []."""
    import base64
    import time

    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    def b64(x: bytes) -> str:
        return base64.urlsafe_b64encode(x).rstrip(b"=").decode()

    now = int(time.time())
    header = b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claim = b64(json.dumps({
        "iss": sa["client_email"], "scope": scope,
        "aud": "https://oauth2.googleapis.com/token",
        "exp": now + 3600, "iat": now}).encode())
    signing_input = f"{header}.{claim}".encode()
    key = serialization.load_pem_private_key(sa["private_key"].encode(), password=None)
    sig = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    jwt = f"{header}.{claim}.{b64(sig)}"
    tok = post_json("https://oauth2.googleapis.com/token",
                    {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                     "assertion": jwt}, form=True)
    return tok["access_token"]


def load_sa(var: str) -> dict | None:
    """Carica un service-account JSON da path o da stringa JSON in env."""
    raw = os.environ.get(var)
    if not raw:
        return None
    if os.path.exists(raw):
        with open(raw, encoding="utf-8") as f:
            return json.load(f)
    return json.loads(raw)
