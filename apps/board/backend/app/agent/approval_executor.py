"""Sprint 9D — execute approved proposals.

When Luigi approves (or edits-and-sends) an approval row created by a
`propose_*` tool, this module materializes the action: actually creates
the lead/task/memo or sends the email via Resend.

Body marker format produced by `app/agent/executor.py`:

    [meta] tool=propose_new_lead
    [meta] payload={"title": "...", ...}

We parse those lines, dispatch to a handler, and return a short
human-readable note that the API layer writes back into
``board_approvals.decision_note``.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from app.services.mailer import send_email
from app.settings import get_settings

log = logging.getLogger(__name__)


# ── Body marker parsing ─────────────────────────────────────────────────────

_TOOL_RE = re.compile(r"^\[meta\]\s*tool=([a-zA-Z0-9_]+)\s*$", re.MULTILINE)
_PAYLOAD_RE = re.compile(r"^\[meta\]\s*payload=(.+)$", re.MULTILINE)


def parse_meta_marker(body: str) -> Tuple[Optional[str], Dict[str, Any]]:
    """Extract `(tool_name, args)` from an approval body. Returns (None, {})
    when no marker is present. Tolerant: malformed JSON → empty args."""
    if not body:
        return None, {}
    tool_match = _TOOL_RE.search(body)
    if not tool_match:
        return None, {}
    tool_name = tool_match.group(1).strip()

    args: Dict[str, Any] = {}
    payload_match = _PAYLOAD_RE.search(body)
    if payload_match:
        raw = payload_match.group(1).strip()
        try:
            args = json.loads(raw)
            if not isinstance(args, dict):
                args = {}
        except (json.JSONDecodeError, ValueError):
            log.warning("approval_executor.payload_parse_failed", extra={"raw": raw[:200]})
            args = {}
    return tool_name, args


# ── Body extraction for edited email drafts ─────────────────────────────────

def extract_edited_email_body(body: str) -> Optional[str]:
    """Pull the markdown body out of a `propose_email_draft` approval body.

    The original template wraps the email between `---` fences, e.g.:

        Subject: ...

        ---
        <body>
        ---

        Rationale:
        ...
    """
    if "---" not in body:
        return None
    parts = body.split("---")
    if len(parts) < 3:
        return None
    # Between the FIRST and SECOND ``---`` lies the email body.
    return parts[1].strip() or None


def extract_edited_subject(body: str) -> Optional[str]:
    m = re.search(r"^Subject:\s*(.+)$", body, re.MULTILINE)
    return m.group(1).strip() if m else None


# ── Main dispatcher ─────────────────────────────────────────────────────────

async def execute_approved_action(
    tool_name: str,
    args: Dict[str, Any],
    approval_id: str,
    *,
    sb=None,
    edited_body: Optional[str] = None,
) -> str:
    """Materialize the action. Returns a human-readable decision note.

    `sb` is injected for testability. Defaults to the cached service-role
    client.
    """
    if sb is None:
        from app.db.client import get_supabase

        sb = get_supabase()

    try:
        if tool_name == "propose_new_lead":
            return _exec_new_lead(sb, args)
        if tool_name == "propose_lead_update":
            return _exec_lead_update(sb, args)
        if tool_name == "propose_email_draft":
            return _exec_email_draft(sb, args, edited_body=edited_body)
        if tool_name == "propose_proposta_commerciale":
            return _exec_proposta(sb, args, edited_body=edited_body)
        if tool_name == "propose_task":
            return _exec_task(sb, args)
        return f"Tool '{tool_name}' non riconosciuto — nessuna azione eseguita."
    except Exception as exc:  # noqa: BLE001
        log.exception("approval_executor.failed", extra={"tool": tool_name, "approval_id": approval_id})
        return f"Esecuzione fallita: {exc}"


# ── Handlers ────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _find_or_create_contact(sb, company: str) -> Optional[str]:
    """Return existing contact id matching company (case-insensitive), or create one."""
    if not company:
        return None
    company = company.strip()
    res = (
        sb.table("board_contacts")
        .select("id, company")
        .ilike("company", company)
        .limit(1)
        .execute()
    )
    rows = res.data or []
    if rows:
        return rows[0]["id"]
    created = (
        sb.table("board_contacts")
        .insert({"company": company})
        .execute()
    )
    cdata = created.data or []
    return cdata[0]["id"] if cdata else None


def _exec_new_lead(sb, args: Dict[str, Any]) -> str:
    contact_id: Optional[str] = args.get("contact_id")
    if not contact_id and args.get("contact_company"):
        contact_id = _find_or_create_contact(sb, str(args["contact_company"]))

    payload: Dict[str, Any] = {
        "title": args.get("title") or "Lead senza titolo",
        "status": args.get("status") or "nuovo",
        "source": args.get("source") or "other",
    }
    if contact_id:
        payload["contact_id"] = contact_id
    if args.get("value_eur") is not None:
        payload["value_eur"] = args["value_eur"]
    if args.get("probability") is not None:
        payload["probability"] = args["probability"]
    if args.get("next_action_at"):
        payload["next_action_at"] = args["next_action_at"]
    if args.get("next_action_note"):
        payload["next_action_note"] = args["next_action_note"]

    res = sb.table("board_leads").insert(payload).execute()
    row = (res.data or [{}])[0]
    lead_id = row.get("id")
    note = f"Lead creato: {lead_id}"
    if contact_id:
        note += f" (contatto: {contact_id})"
    return note


def _exec_lead_update(sb, args: Dict[str, Any]) -> str:
    lead_id = args.get("lead_id")
    fields = args.get("fields_json") or {}
    if not lead_id or not isinstance(fields, dict) or not fields:
        return "Modifica lead saltata: dati incompleti."
    sb.table("board_leads").update(fields).eq("id", lead_id).execute()
    return f"Lead {lead_id} aggiornato ({len(fields)} campi)."


def _exec_email_draft(
    sb, args: Dict[str, Any], *, edited_body: Optional[str] = None
) -> str:
    contact_id = args.get("to_contact_id")
    subject = args.get("subject") or "(senza oggetto)"
    body_md = edited_body or args.get("body_markdown") or ""

    # Look up recipient email
    to_email = None
    contact_name = None
    if contact_id:
        cres = (
            sb.table("board_contacts")
            .select("id, email, person_name, company")
            .eq("id", contact_id)
            .limit(1)
            .execute()
        )
        crows = cres.data or []
        if crows:
            to_email = crows[0].get("email")
            contact_name = crows[0].get("person_name") or crows[0].get("company")

    # Record memo of the sent email regardless.
    memo_payload = {
        "subject": f"Email inviata: {subject}",
        "body": body_md,
        "tags": ["email-inviata", "auto-eseguito"],
    }
    if contact_id:
        memo_payload["contact_id"] = contact_id
    sb.table("board_memos").insert(memo_payload).execute()

    if not to_email:
        return f"Email registrata come memo (contatto {contact_id or '?'} senza indirizzo email)."

    settings = get_settings()
    if not settings.resend_api_key:
        return f"Email pronta per {to_email} ma RESEND_API_KEY non configurato — salvata come memo."

    result = send_email(to=to_email, subject=subject, body_md=body_md)
    if result.get("sent"):
        target = contact_name or to_email
        return f"Email inviata a {target} <{to_email}> (id Resend: {result.get('id')})."
    return f"Invio email fallito: {result.get('reason')}. Bozza salvata come memo."


def _exec_proposta(
    sb, args: Dict[str, Any], *, edited_body: Optional[str] = None
) -> str:
    lead_id = args.get("lead_id")
    body_md = edited_body or args.get("body_markdown") or ""
    memo_payload: Dict[str, Any] = {
        "subject": f"Proposta commerciale (lead {str(lead_id)[:8] if lead_id else '?'})",
        "body": body_md,
        "tags": ["proposta-commerciale", "auto-eseguito"],
    }
    if lead_id:
        memo_payload["lead_id"] = lead_id
    res = sb.table("board_memos").insert(memo_payload).execute()
    memo_id = (res.data or [{}])[0].get("id")
    # Flag the lead so it's visible in the pipeline.
    if lead_id:
        sb.table("board_leads").update(
            {
                "next_action_note": "Proposta commerciale pronta — vedi memos",
                "next_action_at": _now_iso(),
            }
        ).eq("id", lead_id).execute()
    return f"Proposta salvata come memo {memo_id} e lead aggiornato."


def _exec_task(sb, args: Dict[str, Any]) -> str:
    payload: Dict[str, Any] = {
        "title": args.get("title") or "Task senza titolo",
        "priority": args.get("priority") or "media",
        "status": args.get("status") or "todo",
    }
    if args.get("due_at"):
        payload["due_at"] = args["due_at"]
    if args.get("lead_id"):
        payload["lead_id"] = args["lead_id"]
    if args.get("notes"):
        payload["notes"] = args["notes"]
    res = sb.table("board_tasks").insert(payload).execute()
    row = (res.data or [{}])[0]
    return f"Task creato: {row.get('id')}"
