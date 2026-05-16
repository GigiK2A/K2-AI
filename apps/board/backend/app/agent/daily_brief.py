"""Sprint 9B — daily brief generator.

Calls Claude with the read-only subset of Giuseppina's tools and asks for
a short Italian markdown brief. Delivery: save as a memo with the
``brief-mattutino`` tag and email the owner via Resend if configured.
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List

from anthropic import AsyncAnthropic

from app.agent.executor import execute_tool
from app.agent.tools import TOOLS
from app.db.client import get_supabase
from app.services.mailer import send_email
from app.settings import get_settings

log = logging.getLogger(__name__)

BRIEF_MODEL = "claude-haiku-4-5"
MAX_ITERATIONS = 6
MAX_TOKENS = 1500
BRIEF_TAG = "brief-mattutino"

# Only expose READ-only tools to the brief generator.
_READ_ONLY_TOOL_NAMES = {
    "list_leads",
    "get_lead",
    "search_contacts",
    "list_tasks",
    "list_pending_approvals",
    "search_memos",
    "get_revenue_summary",
    "list_meetings",
    "overview_snapshot",
}


def _read_only_tools() -> List[Dict[str, Any]]:
    return [t for t in TOOLS if t.get("name") in _READ_ONLY_TOOL_NAMES]


BRIEF_SYSTEM_PROMPT = """Sei Giuseppina. Produci il brief mattutino per Luigi.

Usa SOLO i tool read-only per raccogliere fatti, poi scrivi un brief
markdown in italiano, conciso (max 250 parole). Sezioni FISSE:

## Brief del {today_iso}

### Numeri
- Revenue MTD: € X
- Lead aperti / per status
- Task aperti / in scadenza / scaduti
- Approvazioni in coda

### Lead che richiedono azione oggi
(elenco breve, max 5, con next_action se presente)

### Task in scadenza nelle prossime 48h
(elenco breve)

### Approvazioni pendenti
(elenco breve dei titoli)

### Prossimo meeting
(uno solo, il più imminente)

### Suggerimento Giuseppina
(una frase pratica: "oggi farei X")

Niente buzzword. Numeri concreti dai tool. Niente HTML.
"""


async def generate_daily_brief() -> str:
    """Run the read-only tool loop and return the markdown brief."""
    settings = get_settings()
    if not settings.anthropic_api_key:
        return "_Brief non generato: ANTHROPIC_API_KEY mancante._"

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    sb = get_supabase()
    today_iso = date.today().isoformat()
    system = BRIEF_SYSTEM_PROMPT.format(today_iso=today_iso)
    tools = _read_only_tools()

    messages: List[Dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                "Genera il brief mattutino di oggi seguendo lo schema indicato. "
                "Usa i tool per recuperare i dati. Non inventare numeri."
            ),
        }
    ]

    full_text = ""

    for _ in range(MAX_ITERATIONS):
        try:
            response = await client.messages.create(
                model=BRIEF_MODEL,
                max_tokens=MAX_TOKENS,
                system=system,
                tools=tools,
                messages=messages,
            )
        except Exception as exc:  # noqa: BLE001
            log.exception("daily_brief.api_error")
            return f"_Brief non generato: {exc}_"

        assistant_blocks: List[Dict[str, Any]] = []
        tool_uses: List[Dict[str, Any]] = []
        for block in response.content:
            btype = getattr(block, "type", None)
            if btype == "text":
                text = block.text or ""
                full_text += text
                assistant_blocks.append({"type": "text", "text": text})
            elif btype == "tool_use":
                tu = {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input or {},
                }
                assistant_blocks.append(tu)
                tool_uses.append(tu)

        messages.append({"role": "assistant", "content": assistant_blocks})

        if not tool_uses or response.stop_reason == "end_turn":
            break

        tool_results: List[Dict[str, Any]] = []
        for tu in tool_uses:
            if tu["name"] not in _READ_ONLY_TOOL_NAMES:
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": tu["id"],
                        "content": json.dumps({"error": "tool non disponibile nel brief"}),
                        "is_error": True,
                    }
                )
                continue
            result = await execute_tool(tu["name"], tu["input"], sb)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": json.dumps(result, ensure_ascii=False, default=str),
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return full_text.strip() or "_Brief vuoto._"


async def deliver_daily_brief() -> Dict[str, Any]:
    """Generate + persist (memo) + email. Returns a delivery report."""
    today_iso = date.today().isoformat()
    brief = await generate_daily_brief()

    sb = get_supabase()
    memo_subject = f"Brief mattutino — {today_iso}"
    memo_res = (
        sb.table("board_memos")
        .insert(
            {
                "subject": memo_subject,
                "body": brief,
                "tags": [BRIEF_TAG, "auto-generato"],
            }
        )
        .execute()
    )
    memo_id = (memo_res.data or [{}])[0].get("id")

    settings = get_settings()
    email_result: Dict[str, Any] = {"sent": False, "reason": "disabled"}
    if settings.resend_api_key and settings.board_owner_email:
        email_result = send_email(
            to=settings.board_owner_email,
            subject=f"K2-Board — {memo_subject}",
            body_md=brief,
        )

    report = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "brief_chars": len(brief),
        "memo_id": memo_id,
        "memo_saved": memo_id is not None,
        "email_sent": bool(email_result.get("sent")),
        "email_detail": email_result,
    }
    log.info("daily_brief.delivered", extra=report)
    return report
