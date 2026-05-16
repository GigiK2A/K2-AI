"""Sprint 9C — email triage.

Provider-agnostic surface. Two providers:

* ``StubProvider`` — reads from ``board_inbox_pending`` (manual paste).
  Always available.
* ``GmailOAuthProvider`` — full Gmail API via OAuth2 refresh-token. Only
  available when ``GOOGLE_CLIENT_ID``, ``GOOGLE_CLIENT_SECRET`` and
  ``GOOGLE_REFRESH_TOKEN`` are all set.

Classification is a single Claude haiku call returning JSON. The action
dispatcher then routes to add_memo / propose_new_lead / propose_task or
no-ops on ``ignora``.
"""
from __future__ import annotations

import base64
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Protocol, Tuple

import httpx
from anthropic import AsyncAnthropic

from app.agent.executor import (
    _add_memo,
    _propose_new_lead,
    _propose_task,
)
from app.db.client import get_supabase
from app.settings import get_settings

log = logging.getLogger(__name__)

TRIAGE_MODEL = "claude-haiku-4-5"
TRIAGE_TABLE = "board_inbox_pending"


# ── DTO ──────────────────────────────────────────────────────────────────────

@dataclass
class InboundEmail:
    id: str
    from_email: str
    from_name: str
    subject: str
    body: str
    received_at: datetime

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["received_at"] = self.received_at.isoformat()
        return d


# ── Providers ────────────────────────────────────────────────────────────────

class EmailProvider(Protocol):
    name: str

    async def fetch_recent(self, since: datetime) -> List[InboundEmail]: ...

    async def mark_triaged(self, email_id: str, result: Dict[str, Any]) -> None: ...


class StubProvider:
    """Reads from a Supabase staging table the user can populate by hand."""

    name = "stub"

    def __init__(self, sb=None) -> None:
        self._sb = sb

    def _client(self):
        return self._sb or get_supabase()

    async def fetch_recent(self, since: datetime) -> List[InboundEmail]:
        sb = self._client()
        res = (
            sb.table(TRIAGE_TABLE)
            .select("*")
            .is_("triaged_at", "null")
            .gte("received_at", since.isoformat())
            .order("received_at", desc=True)
            .limit(50)
            .execute()
        )
        rows = res.data or []
        out: List[InboundEmail] = []
        for r in rows:
            try:
                received = datetime.fromisoformat(
                    str(r["received_at"]).replace("Z", "+00:00")
                )
            except (KeyError, ValueError):
                received = datetime.now(tz=timezone.utc)
            out.append(
                InboundEmail(
                    id=str(r["id"]),
                    from_email=r.get("from_email") or "",
                    from_name=r.get("from_name") or "",
                    subject=r.get("subject") or "",
                    body=r.get("body") or "",
                    received_at=received,
                )
            )
        return out

    async def mark_triaged(self, email_id: str, result: Dict[str, Any]) -> None:
        sb = self._client()
        sb.table(TRIAGE_TABLE).update(
            {
                "triaged_at": datetime.now(tz=timezone.utc).isoformat(),
                "triage_result": result,
            }
        ).eq("id", email_id).execute()


class GmailOAuthProvider:
    """Gmail API via OAuth2 refresh token. Read-only `users.messages.list/get`."""

    name = "gmail"

    def __init__(self) -> None:
        s = get_settings()
        self.client_id = s.google_client_id
        self.client_secret = s.google_client_secret
        self.refresh_token = s.google_refresh_token

    @property
    def available(self) -> bool:
        return bool(self.client_id and self.client_secret and self.refresh_token)

    async def _access_token(self) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            r.raise_for_status()
            return r.json()["access_token"]

    async def fetch_recent(self, since: datetime) -> List[InboundEmail]:
        token = await self._access_token()
        headers = {"Authorization": f"Bearer {token}"}
        # Gmail query syntax: `after:` accepts epoch seconds.
        query = f"in:inbox after:{int(since.timestamp())}"

        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            list_resp = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                params={"q": query, "maxResults": 25},
            )
            list_resp.raise_for_status()
            ids = [m["id"] for m in (list_resp.json().get("messages") or [])]

            out: List[InboundEmail] = []
            for mid in ids:
                msg_resp = await client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}",
                    params={"format": "full"},
                )
                if msg_resp.status_code != 200:
                    continue
                out.append(_parse_gmail_message(msg_resp.json()))
            return out

    async def mark_triaged(self, email_id: str, result: Dict[str, Any]) -> None:
        # Gmail provider has no local state to write — triage results are
        # captured in the actions (memos/leads/tasks) themselves. We could
        # apply a label here in a future iteration.
        return None


def _parse_gmail_message(msg: Dict[str, Any]) -> InboundEmail:
    headers = {
        h["name"].lower(): h["value"]
        for h in msg.get("payload", {}).get("headers", [])
    }
    subject = headers.get("subject", "")
    from_raw = headers.get("from", "")
    from_email = ""
    from_name = ""
    if "<" in from_raw and ">" in from_raw:
        from_name = from_raw.split("<", 1)[0].strip().strip('"')
        from_email = from_raw.split("<", 1)[1].rstrip(">").strip()
    else:
        from_email = from_raw.strip()

    body = _extract_gmail_body(msg.get("payload", {})) or msg.get("snippet", "")
    try:
        ts_ms = int(msg.get("internalDate", "0"))
        received = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    except (TypeError, ValueError):
        received = datetime.now(tz=timezone.utc)

    return InboundEmail(
        id=msg.get("id", ""),
        from_email=from_email,
        from_name=from_name,
        subject=subject,
        body=body,
        received_at=received,
    )


def _extract_gmail_body(payload: Dict[str, Any]) -> str:
    """Best-effort plain-text body extraction (recursive on multipart)."""
    if not payload:
        return ""
    mime = payload.get("mimeType", "")
    data = (payload.get("body") or {}).get("data")
    if data and mime.startswith("text/"):
        try:
            decoded = base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")
            if mime == "text/plain":
                return decoded
            # Crude HTML stripper for text/html fallback.
            import re as _re
            return _re.sub(r"<[^>]+>", "", decoded)
        except (ValueError, UnicodeDecodeError):
            return ""
    for part in payload.get("parts") or []:
        text = _extract_gmail_body(part)
        if text:
            return text
    return ""


# ── Classification ──────────────────────────────────────────────────────────

_TRIAGE_SYSTEM = """Sei un classificatore di email per Giuseppina (K2-AI).
Classifica l'email in UNA categoria:
- ignora: newsletter, spam, conferme automatiche, notifiche di sistema
- memo: contiene informazione utile da ricordare ma nessuna azione richiesta
- lead: richiesta commerciale / opportunità (preventivo, info su servizi)
- task: cosa concreta da fare (richiesta operativa)

Output SOLO JSON valido senza testo aggiuntivo, schema:
{
  "category": "ignora|memo|lead|task",
  "summary": "una frase italiana <120 caratteri",
  "suggested_action": "una frase italiana su cosa dovrebbe fare Luigi"
}
"""


async def classify_email(email: InboundEmail) -> Dict[str, Any]:
    """Returns ``{category, summary, suggested_action}``. Falls back to
    ``ignora`` on any error so the loop never crashes mid-batch."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        return {
            "category": "ignora",
            "summary": "ANTHROPIC_API_KEY mancante",
            "suggested_action": "configurare la chiave",
        }

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    user_payload = (
        f"From: {email.from_name} <{email.from_email}>\n"
        f"Subject: {email.subject}\n\n"
        f"{email.body[:4000]}"
    )
    try:
        resp = await client.messages.create(
            model=TRIAGE_MODEL,
            max_tokens=400,
            system=_TRIAGE_SYSTEM,
            messages=[{"role": "user", "content": user_payload}],
        )
        raw = ""
        for block in resp.content:
            if getattr(block, "type", None) == "text":
                raw += block.text or ""
        raw = raw.strip()
        # Tolerate ```json fences``.
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.lower().startswith("json"):
                raw = raw[4:].lstrip()
        parsed = json.loads(raw)
        cat = str(parsed.get("category") or "ignora").lower()
        if cat not in {"ignora", "memo", "lead", "task"}:
            cat = "ignora"
        return {
            "category": cat,
            "summary": str(parsed.get("summary") or "")[:200],
            "suggested_action": str(parsed.get("suggested_action") or "")[:300],
        }
    except Exception as exc:  # noqa: BLE001
        log.warning("triage.classify_failed", extra={"email_id": email.id, "exc": str(exc)})
        return {
            "category": "ignora",
            "summary": f"classificazione fallita: {exc}",
            "suggested_action": "rivedere manualmente",
        }


# ── Action executor ─────────────────────────────────────────────────────────

def execute_email_action(
    sb,
    action: Dict[str, Any],
    email: InboundEmail,
) -> Dict[str, Any]:
    category = action["category"]
    if category == "ignora":
        return {"category": "ignora", "result": "skipped"}

    if category == "memo":
        result = _add_memo(
            sb,
            {
                "subject": f"[email] {email.subject}",
                "body": (
                    f"Da: {email.from_name} <{email.from_email}>\n"
                    f"Ricevuto: {email.received_at.isoformat()}\n\n"
                    f"{email.body[:4000]}\n\n"
                    f"---\nGiuseppina: {action.get('summary', '')}"
                ),
                "tags": ["email-triage", "memo-auto"],
            },
        )
        return {"category": "memo", "result": result}

    if category == "lead":
        company = email.from_name or email.from_email.split("@")[-1]
        lead_args = {
            "title": email.subject or f"Richiesta da {company}",
            "source": "contact_form",
            "contact_company": company,
            "rationale": action.get("suggested_action") or action.get("summary") or "Email in arrivo",
        }
        result = _propose_new_lead(sb, lead_args)
        return {"category": "lead", "result": result}

    if category == "task":
        task_args = {
            "title": action.get("suggested_action") or f"Gestire email: {email.subject}",
            "priority": "media",
            "rationale": action.get("summary") or "Da email in arrivo",
        }
        result = _propose_task(sb, task_args)
        return {"category": "task", "result": result}

    return {"category": category, "result": "unknown_category"}


# ── Orchestration ───────────────────────────────────────────────────────────

async def triage_inbox(
    provider: EmailProvider,
    *,
    hours: int = 24,
    sb=None,
    classifier: Optional[Callable[[InboundEmail], Awaitable[Dict[str, Any]]]] = None,
) -> Dict[str, Any]:
    sb = sb or get_supabase()
    since = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    classify = classifier or classify_email

    emails = await provider.fetch_recent(since)
    actions: List[Dict[str, Any]] = []
    for email in emails:
        action = await classify(email)
        outcome = execute_email_action(sb, action, email)
        record = {
            "email_id": email.id,
            "from": email.from_email,
            "subject": email.subject,
            "category": action["category"],
            "summary": action.get("summary"),
            "outcome": outcome.get("result"),
        }
        actions.append(record)
        try:
            await provider.mark_triaged(email.id, record)
        except Exception:  # noqa: BLE001
            log.warning("triage.mark_failed", extra={"email_id": email.id})

    return {
        "provider": provider.name,
        "processed": len(emails),
        "actions": actions,
    }


def list_providers() -> Dict[str, Any]:
    s = get_settings()
    gmail = GmailOAuthProvider()
    return {
        "stub": {"available": True, "name": "Stub (Supabase board_inbox_pending)"},
        "gmail": {
            "available": gmail.available,
            "name": "Gmail OAuth",
            "missing_env": [
                k
                for k, v in (
                    ("GOOGLE_CLIENT_ID", s.google_client_id),
                    ("GOOGLE_CLIENT_SECRET", s.google_client_secret),
                    ("GOOGLE_REFRESH_TOKEN", s.google_refresh_token),
                )
                if not v
            ],
        },
        "triage_enabled": s.email_triage_enabled,
        "cron": s.email_triage_cron,
    }


def build_default_provider() -> Tuple[EmailProvider, str]:
    gmail = GmailOAuthProvider()
    if gmail.available:
        return gmail, "gmail"
    return StubProvider(), "stub"
