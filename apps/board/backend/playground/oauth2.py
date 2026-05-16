"""Helper: obtain a Gmail OAuth2 refresh token for the triage provider.

Run locally (NOT on Railway). Opens a browser, lets you sign in to the
Gmail account Giuseppina will read from, prints `client_id`/`secret`/
`refresh_token` ready to drop into ``.env``.

Usage:
    python playground/oauth2.py --client-id ... --client-secret ...

If the args are omitted we read from the GOOGLE_CLIENT_ID /
GOOGLE_CLIENT_SECRET env vars.

Scopes: gmail.readonly + gmail.modify (the latter is needed if/when we
start applying labels to triaged messages).
"""
from __future__ import annotations

import argparse
import http.server
import json
import os
import secrets
import socket
import threading
import urllib.parse
import webbrowser

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


def _free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _capture_code(port: int) -> str:
    holder: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            qs = urllib.parse.urlparse(self.path).query
            params = dict(urllib.parse.parse_qsl(qs))
            holder.update(params)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<h1>OK</h1>Puoi chiudere questa finestra.")

        def log_message(self, *_a, **_k) -> None:  # noqa: D401
            pass

    httpd = http.server.HTTPServer(("127.0.0.1", port), Handler)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    while "code" not in holder and "error" not in holder:
        pass
    httpd.shutdown()
    if "error" in holder:
        raise SystemExit(f"OAuth error: {holder['error']}")
    return holder["code"]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--client-id", default=os.environ.get("GOOGLE_CLIENT_ID"))
    p.add_argument("--client-secret", default=os.environ.get("GOOGLE_CLIENT_SECRET"))
    args = p.parse_args()
    if not args.client_id or not args.client_secret:
        raise SystemExit("Set --client-id/--client-secret or GOOGLE_CLIENT_ID/SECRET env.")

    port = _free_port()
    redirect_uri = f"http://127.0.0.1:{port}"
    state = secrets.token_urlsafe(16)
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode(
            {
                "client_id": args.client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": " ".join(SCOPES),
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
            }
        )
    )
    print(f"Apertura browser…\n{auth_url}\n")
    webbrowser.open(auth_url)
    code = _capture_code(port)

    import urllib.request

    body = urllib.parse.urlencode(
        {
            "client_id": args.client_id,
            "client_secret": args.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        }
    ).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        token_data = json.loads(resp.read().decode())

    print("\n── INCOLLARE IN .env ──────────────────────────────")
    print(f"GOOGLE_CLIENT_ID={args.client_id}")
    print(f"GOOGLE_CLIENT_SECRET={args.client_secret}")
    print(f"GOOGLE_REFRESH_TOKEN={token_data.get('refresh_token')}")
    print("───────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
