from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from core.text import markdown_to_plain_text, truncate_text

PRIMARY_BOT_NAME = "Giuseppina"

_CONTEXT_BY_AGENT = {
    "chief_of_staff": "Briefing operativo",
    "project_operations": "Briefing operativo",
    "knowledge": "Briefing operativo",
    "finance_kpi": "KPI",
    "market_intelligence": "Analisi mercato",
    "sales_enablement": "Pipeline commerciale",
    "lead_generation": "Pipeline commerciale",
    "outreach": "Pipeline commerciale",
    "content_engine": "Contenuti",
    "solution_architect": "Architettura",
    "legal": "Legale",
    "geo_seo": "Geo SEO",
}

_CONTEXT_BY_SCHEDULER_JOB = {
    "daily_brief": "Briefing operativo",
    "weekly_plan": "Piano settimanale",
    "kpi_update": "KPI",
    "market_pulse": "Analisi mercato",
    "task_deadline_reminder": "Briefing operativo",
    "approval_reminder": "Briefing operativo",
}

_TECHNICAL_ERROR_PATTERNS = (
    "database notion non trovato",
    "log ai",
    "traceback",
    "supabase",
    "notion",
    "scheduler:",
    "chief_of_staff",
    "finance_kpi",
    "market_intelligence",
    "orchestrator",
)


# ── Personas del board ────────────────────────────────────────────────────────
# `visible_agent_label` maschera tutti gli agenti come "Giuseppina" perché verso
# il fondatore il board ha una voce unica. Ma quando il fondatore sceglie
# ESPLICITAMENTE con chi parlare (menu /board, roundtable) mostriamo i nomi veri.
# Queste sono le 9 personas canoniche (allineate ad AGENT_REGISTRY).
BOARD_MEMBERS: list[dict[str, str]] = [
    {"agent": "orchestrator", "name": "Giuseppina", "emoji": "🎯", "area": "Regia del board"},
    {"agent": "chief_of_staff", "name": "Gino", "emoji": "📋", "area": "Operazioni"},
    {"agent": "content_engine", "name": "Genoveffa", "emoji": "✍️", "area": "Marketing & contenuti"},
    {"agent": "market_intelligence", "name": "Market Intelligence", "emoji": "🔍", "area": "Analisi di mercato"},
    {"agent": "sales_enablement", "name": "Peppe", "emoji": "🚀", "area": "Vendite & pipeline"},
    {"agent": "solution_architect", "name": "Archimede", "emoji": "🏗️", "area": "Soluzioni & delivery"},
    {"agent": "finance_kpi", "name": "Ragionier Ugo", "emoji": "💰", "area": "Conti & KPI"},
    {"agent": "legal", "name": "Avvocata Pina", "emoji": "⚖️", "area": "Legale"},
    {"agent": "geo_seo", "name": "Geografino", "emoji": "🌍", "area": "GEO & SEO"},
]

_BOARD_BY_AGENT: dict[str, dict[str, str]] = {member["agent"]: member for member in BOARD_MEMBERS}


def _canonical_agent_key(agent_name: Any) -> str:
    """Normalizza un nome agente (anche alias) alla persona canonica del board."""
    raw = str(agent_name or "").strip().lower()
    if raw.startswith("scheduler:"):
        raw = raw.split(":", 1)[1]
    if raw in _BOARD_BY_AGENT:
        return raw
    try:
        from core.orchestrator import resolve_agent_name
        from db.models import AgentName

        return resolve_agent_name(AgentName(raw)).value
    except Exception:
        return raw


def board_member(agent_name: Any) -> dict[str, str] | None:
    return _BOARD_BY_AGENT.get(_canonical_agent_key(agent_name))


def board_member_name(agent_name: Any) -> str:
    member = board_member(agent_name)
    return member["name"] if member else PRIMARY_BOT_NAME


def board_member_label(agent_name: Any, with_area: bool = False) -> str:
    """Etichetta col nome REALE dell'agente (per il menu /board e il roundtable)."""
    member = board_member(agent_name)
    if not member:
        return PRIMARY_BOT_NAME
    label = f"{member['emoji']} {member['name']}"
    if with_area:
        label += f" · {member['area']}"
    return label


def visible_agent_label(agent_name: Any, context: str | None = None) -> str:
    raw = str(agent_name or "").strip().lower()
    if raw.startswith("scheduler:"):
        raw = raw.split(":", 1)[1]

    ctx = context or _CONTEXT_BY_AGENT.get(raw) or _CONTEXT_BY_SCHEDULER_JOB.get(raw)
    if ctx:
        return f"{PRIMARY_BOT_NAME} - {ctx}"
    return PRIMARY_BOT_NAME


def sanitize_user_error_message(error: Any) -> str:
    text = markdown_to_plain_text(error).strip()
    lowered = text.lower()
    if not text:
        return "Ho avuto un intoppo operativo. Riprovo in modo sicuro."
    if any(pattern in lowered for pattern in _TECHNICAL_ERROR_PATTERNS):
        return "C'e stato un problema interno, ma sto continuando in modalita sicura."
    return "Ho avuto un intoppo operativo. Riprova tra poco."


def smart_truncate(text: Any, max_len: int = 220, suffix: str = "…") -> str:
    plain = markdown_to_plain_text(text)
    if len(plain) <= max_len:
        return plain
    window = max_len - len(suffix)
    if window <= 0:
        return suffix[:max_len]

    cut = plain[:window]
    sentence = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if sentence > max(80, window // 2):
        return cut[: sentence + 1].rstrip() + suffix
    newline = cut.rfind("\n")
    if newline > max(80, window // 2):
        return cut[:newline].rstrip() + suffix
    space = cut.rfind(" ")
    if space > 0:
        return cut[:space].rstrip() + suffix
    return truncate_text(plain, max_len, suffix=suffix)


def clean_preview(text: Any, max_len: int = 220) -> str:
    plain = markdown_to_plain_text(text)
    normalized = re.sub(r"\s+\n", "\n", plain)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    normalized = re.sub(r"[ \t]{2,}", " ", normalized)
    cleaned_lines = []
    for line in normalized.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.lower().startswith(("id:", "task id:", "approval id:", "traceback")):
            continue
        cleaned_lines.append(stripped)
    joined = "\n".join(cleaned_lines).strip() or "Anteprima non disponibile."
    return smart_truncate(joined, max_len=max_len)


def approval_is_recent(created_at: Any, max_age_hours: int = 72) -> bool:
    if not created_at:
        return True
    try:
        raw = str(created_at).replace("Z", "+00:00")
        created_dt = datetime.fromisoformat(raw)
        if created_dt.tzinfo is None:
            created_dt = created_dt.replace(tzinfo=UTC)
        age_h = (datetime.now(UTC) - created_dt).total_seconds() / 3600
        return age_h <= max_age_hours
    except Exception:
        return True
