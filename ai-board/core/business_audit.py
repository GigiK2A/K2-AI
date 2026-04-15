"""
Audit trail business leggibile da umano.

Registra ogni azione significativa sul board in formato comprensibile,
non solo tecnico. Quando qualcuno chiede "chi ha spostato questo cliente?"
o "cosa ha fatto il bot ieri?", questo log risponde.

Campi chiave:
- actor:       chi ha originato la richiesta (founder, scheduler, agent_name)
- intent:      linguaggio naturale della richiesta originale
- action:      cosa è stato eseguito (verbo + oggetto)
- entity_type: tipo di entità modificata (task, lead, client, memory)
- entity_name: nome human-readable dell'entità
- outcome:     success | error | confirmed | cancelled | pending_confirmation
- details:     dizionario opzionale con dati aggiuntivi

Storage:
- Notion attivo: scrive su Log AI con action field arricchito
- Supabase: scrive su tabella business_audit (se disponibile)
- Fallback: solo loguru (mai silenzioso)
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from loguru import logger


def log_business_action(
    action: str,
    entity_type: str,
    entity_name: str,
    outcome: str = "success",
    actor: str = "founder",
    intent: str = "",
    details: dict[str, Any] | None = None,
    agent: str = "orchestrator",
) -> None:
    """
    Registra un'azione business nel trail di audit.

    Args:
        action:      Cosa è stato fatto, es. "Lead 'Mario Rossi' aggiunto alla pipeline"
        entity_type: Tipo entità: task | lead | client | memory | pipeline
        entity_name: Nome leggibile dell'entità, es. "Mario Rossi"
        outcome:     success | error | confirmed | cancelled | pending_confirmation
        actor:       Chi ha originato: founder | scheduler | orchestrator | <agent_name>
        intent:      Testo originale della richiesta, se disponibile
        details:     Dati aggiuntivi opzionali
        agent:       Nome tecnico dell'agente che ha eseguito
    """
    timestamp = datetime.now(UTC).isoformat()
    entry: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "actor": actor,
        "agent": agent,
        "intent": intent[:500] if intent else "",
        "action": action[:500],
        "entity_type": entity_type,
        "entity_name": entity_name[:200],
        "outcome": outcome,
        "details": details or {},
    }

    # Loguru — sempre
    log_line = (
        f"[business_audit] {outcome.upper()} | {actor} → {action} "
        f"[{entity_type}: {entity_name}]"
    )
    if outcome == "error":
        logger.warning(log_line)
    else:
        logger.info(log_line)

    # Prova Notion primo, poi Supabase
    try:
        from core import notion_board
        if notion_board.notion_enabled():
            _write_to_notion_log(entry)
            return
    except Exception as exc:
        logger.debug(f"[business_audit] Notion write fallita: {exc}")

    try:
        _write_to_supabase(entry)
    except Exception as exc:
        logger.debug(f"[business_audit] Supabase write fallita: {exc}")


def _write_to_notion_log(entry: dict[str, Any]) -> None:
    """Scrive su Log AI Notion con action arricchita."""
    from core import notion_board

    # Construisce action leggibile
    action_label = (
        f"[{entry['entity_type'].upper()}] {entry['action']} "
        f"— {entry['outcome']}"
    )
    if entry.get("actor") and entry["actor"] != "orchestrator":
        action_label += f" (da: {entry['actor']})"

    output_summary = entry["action"]
    if entry.get("intent"):
        output_summary = f"Richiesta: {entry['intent'][:200]}\nEseguito: {entry['action']}"
    if entry.get("details"):
        import json
        details_str = json.dumps(entry["details"], ensure_ascii=False, default=str)[:300]
        output_summary += f"\nDettagli: {details_str}"

    notion_board.create_agent_log(
        agent=entry["agent"],
        task_id=None,
        action=action_label[:100],
        output_summary=output_summary[:500],
        status="success" if entry["outcome"] in ("success", "confirmed") else "error",
        duration_ms=0,
        tokens_used=None,
        llm_provider=None,
        llm_model=None,
        requires_approval=False,
    )


def _write_to_supabase(entry: dict[str, Any]) -> None:
    """Scrive su tabella business_audit Supabase (se esiste)."""
    from db.client import get_service_client
    client = get_service_client()
    try:
        client.table("business_audit").insert({
            "id": entry["id"],
            "timestamp": entry["timestamp"],
            "actor": entry["actor"],
            "agent": entry["agent"],
            "intent": entry["intent"],
            "action": entry["action"],
            "entity_type": entry["entity_type"],
            "entity_name": entry["entity_name"],
            "outcome": entry["outcome"],
            "details": entry["details"],
        }).execute()
    except Exception as exc:
        # Tabella potrebbe non esistere ancora — non è un errore bloccante
        logger.debug(f"[business_audit] Supabase insert fallita (tabella forse mancante): {exc}")
