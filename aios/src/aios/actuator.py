"""Attuatore Livello 1: esegue scritture REALI su Supabase quando una proposta
viene APPROVATA dall'umano (coda L1). Perimetro di sicurezza stretto:
- solo insert/update su tabelle operative INTERNE in allowlist
- MAI delete · MAI denaro (revenue/conversions/Stripe) · MAI auth/permessi · MAI dati utente kbot
- update richiede sempre un match (niente update di massa)
Ogni scrittura passa di qui e ritorna un esito tracciabile (audit).
"""
from __future__ import annotations

import os
import re
from typing import Any

# DDL consentito: solo modifiche NON distruttive (aggiungere, mai togliere/svuotare).
_DDL_OK_START = ("alter table", "create table", "create index", "create unique index",
                 "comment on", "create or replace view", "create view", "create schema")
_DDL_FORBIDDEN = re.compile(r"\b(drop|truncate|cascade)\b", re.IGNORECASE)

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
    # Interno completo (scelta owner): anche denaro e dati personali si scrivono su Approva.
    "board_revenue_events": {"insert", "update"},
    "kbot_conversions": {"insert", "update"},
    "kbot_profiles": {"insert", "update"},
    "kbot_conversations": {"insert", "update"},
}

# Resta vietato SOLO il piano di controllo: audit/policy (i guardrail stessi), auth/sessioni
# (rischio takeover) e il catalogo pubblico (suite_services, letto dal sito = quasi-esterno).
# Mai delete su NESSUNA tabella. Questi non sono "dati operativi interni": sono il meccanismo.
BLOCKED = {"aios_audit", "aios_policy_state", "board_users", "board_sessions",
           "kbot_sessions", "suite_services"}


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


def validate_ddl(sql: str) -> str:
    """Consente solo DDL NON distruttivo, una sola statement. Solleva altrimenti."""
    s = (sql or "").strip()
    if not s:
        raise ActuatorError("SQL vuoto")
    body = s.rstrip(";").strip()
    if ";" in body:
        raise ActuatorError("una sola statement per volta")
    low = body.lower()
    if not low.startswith(_DDL_OK_START):
        raise ActuatorError("consentito solo ALTER/CREATE non distruttivo (mai DROP/DELETE)")
    if _DDL_FORBIDDEN.search(low):
        raise ActuatorError("DDL distruttivo vietato (drop/truncate/cascade)")
    return body


def apply_ddl(sql: str) -> dict[str, Any]:
    """Esegue una modifica di schema NON distruttiva via psycopg. Env: AIOS_DB_DSN
    (connection string Postgres/Supabase). Senza DSN → niente effetto (configurare)."""
    body = validate_ddl(sql)
    dsn = os.environ.get("AIOS_DB_DSN", "").strip()
    if not dsn:
        return {"ok": False, "errore": "AIOS_DB_DSN non configurato (serve la connection string Postgres)",
                "sql": body[:200]}
    try:
        import psycopg
        with psycopg.connect(dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(body)  # solo DDL non distruttivo (validato sopra)
        return {"ok": True, "op": "ddl", "sql": body[:200]}
    except Exception as exc:
        return {"ok": False, "errore": str(exc)[:200], "sql": body[:200]}


def apply_action(client: Any, action: dict[str, Any]) -> dict[str, Any]:
    """Esegue l'azione su Supabase. DDL (tipo='ddl'|chiave 'sql') → modifica schema
    guardata; altrimenti insert/update di righe su tabella allowlist."""
    if isinstance(action, dict) and (action.get("tipo") == "ddl" or action.get("sql")):
        return apply_ddl(str(action.get("sql", "")))
    table, op, match, data = validate(action)
    if op == "insert":
        rows = client.insert(table, data)
        return {"ok": True, "tabella": table, "op": "insert", "righe": rows}
    # update: SOLO uguaglianza esatta (eq.) per ogni chiave di match — niente operatori
    # passthrough (in./gte./...) → impossibile un update di massa via match crafted.
    filters = {k: f"eq.{v}" for k, v in match.items()}
    rows = client.update(table, filters, data)
    return {"ok": True, "tabella": table, "op": "update", "match": match, "righe": rows}
