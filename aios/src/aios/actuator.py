"""Attuatore Livello 1: esegue scritture REALI su Supabase quando una proposta
viene APPROVATA dall'umano (coda L1). Perimetro di sicurezza stretto:
- solo insert/update su tabelle operative INTERNE in allowlist
- MAI delete · MAI denaro (revenue/conversions/Stripe) · MAI auth/permessi · MAI dati utente kbot
- update richiede sempre un match (niente update di massa)
Ogni scrittura passa di qui e ritorna un esito tracciabile (audit).
"""
from __future__ import annotations

from typing import Any

# tabella -> operazioni consentite. Nessuna 'delete' è mai consentita.
ALLOWLIST: dict[str, set[str]] = {
    "pipeline_leads": {"insert", "update"},
    "invoices": {"insert", "update"},
    "finance_journal": {"insert"},
    "board_cost_items": {"insert", "update"},
    "board_tasks": {"insert", "update"},
    "aios_content_calendar": {"insert", "update"},
    "project_tasks": {"insert", "update"},
    "project_phases": {"update"},
    "candidates": {"insert", "update"},
    "employees": {"insert", "update"},
    "legal_documents": {"insert", "update"},
    "privacy_registro_trattamenti": {"insert"},
    "vendors": {"insert", "update"},
    "shared_memory": {"insert", "update"},
    # Operations
    "team_members": {"insert", "update"},
    "change_requests": {"insert", "update"},
    "project_tools": {"insert", "update"},
    # Legal
    "trademarks": {"insert", "update"},
    "corporate_acts": {"insert", "update"},
    "disputes": {"insert", "update"},
    "insurance_policies": {"insert", "update"},
    "compliance_training": {"insert", "update"},
    "policy_register": {"insert", "update"},
    # HR
    "leave_requests": {"insert", "update"},
    "performance_reviews": {"insert", "update"},
    "skills_matrix": {"insert", "update"},
    "training_records": {"insert", "update"},
    "safety_compliance": {"insert", "update"},
    "offboarding_events": {"insert", "update"},
    "hr_analytics_snapshots": {"insert", "update"},
}

# tabelle esplicitamente vietate alla scrittura (denaro / dati utente / catalogo / auth)
BLOCKED = {"board_revenue_events", "kbot_conversions", "kbot_sessions", "kbot_profiles",
           "kbot_conversations", "suite_services", "aios_audit", "aios_policy_state",
           "board_users", "board_sessions"}


class ActuatorError(RuntimeError):
    pass


def validate(action: dict[str, Any]) -> tuple[str, str, dict, dict]:
    """Valida un'azione e ritorna (tabella, op, match, dati). Solleva se fuori perimetro."""
    if not isinstance(action, dict):
        raise ActuatorError("azione non valida")
    table = str(action.get("tabella") or action.get("table") or "").strip()
    op = str(action.get("op") or action.get("operazione") or "").strip().lower()
    data = action.get("dati") or action.get("row") or action.get("patch") or {}
    match = action.get("match") or action.get("filtri") or {}
    if table in BLOCKED:
        raise ActuatorError(f"tabella vietata alla scrittura: {table}")
    if table not in ALLOWLIST:
        raise ActuatorError(f"tabella non in allowlist: {table}")
    if op not in ALLOWLIST[table]:
        raise ActuatorError(f"operazione '{op}' non consentita su {table}")
    if op == "delete":
        raise ActuatorError("delete mai consentita")
    if not isinstance(data, dict) or not data:
        raise ActuatorError("dati mancanti")
    if op == "update" and (not isinstance(match, dict) or not match):
        raise ActuatorError("update richiede un match (niente update di massa)")
    return table, op, match, data


def apply_action(client: Any, action: dict[str, Any]) -> dict[str, Any]:
    """Esegue l'azione validata su Supabase. Ritorna {ok, tabella, op, ...}."""
    table, op, match, data = validate(action)
    if op == "insert":
        rows = client.insert(table, data)
        return {"ok": True, "tabella": table, "op": "insert", "righe": rows}
    # update: filtri PostgREST eq.<valore>
    filters = {k: (v if str(v).startswith(("eq.", "in.", "gte.", "lte."))
                   else f"eq.{v}") for k, v in match.items()}
    rows = client.update(table, filters, data)
    return {"ok": True, "tabella": table, "op": "update", "match": match, "righe": rows}
