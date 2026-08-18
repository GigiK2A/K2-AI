"""Attuatore Livello 1: esegue azioni REALI quando una proposta viene APPROVATA
dall'umano (coda L1). Sotto approvazione l'agente può fare "tutto", entro il perimetro:
- insert/update/delete su tabelle operative INTERNE in allowlist
- azioni ESTERNE (pubblica/invia/social/gestionale) instradate a n8n (canale:'n8n')
- update e delete richiedono SEMPRE un match (niente operazioni di massa)
- MAI su control-plane (audit/policy/auth/sessioni/catalogo) — BLOCKED
- MAI delete su registri immutabili/contabili/GDPR — _APPEND_ONLY
- DDL solo non distruttivo (mai drop/truncate/cascade)
Ogni azione passa di qui e ritorna un esito tracciabile (audit).
"""
from __future__ import annotations

import os
import re
from typing import Any

# DDL consentito: solo modifiche NON distruttive (aggiungere, mai togliere/svuotare).
_DDL_OK_START = ("alter table", "create table", "create index", "create unique index",
                 "comment on", "create or replace view", "create view", "create schema")
_DDL_FORBIDDEN = re.compile(r"\b(drop|truncate|cascade)\b", re.IGNORECASE)

# tabella -> operazioni base consentite (insert/update). La delete è gestita a parte
# in validate(): permessa con match su queste tabelle, TRANNE quelle in _APPEND_ONLY.
ALLOWLIST: dict[str, set[str]] = {
    "pipeline_leads": {"insert", "update"},
    "invoices": {"insert", "update"},
    "finance_journal": {"insert"},
    "board_cost_items": {"insert", "update"},
    "board_tasks": {"insert", "update"},
    "aios_goals": {"insert", "update"},   # obiettivi (goal ancestry): proposti via approva
    "aios_content_calendar": {"insert", "update"},
    "marketing_prospects": {"insert", "update"},
    "marketing_competitors": {"insert", "update"},
    "email_messages": {"insert", "update"},
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
           "kbot_sessions", "suite_services",
           # Piano di controllo billing: solo il meter di sistema li scrive, mai gli agenti.
           "aios_cost_ledger", "aios_budget_state", "aios_agent_budgets",
           # Heartbeat: lo scrive solo il loop di autonomia, non gli agenti.
           "aios_heartbeats"}

# Registri immutabili / contabili: insert e update sì, ma MAI delete (servono per
# audit, contabilità, GDPR art.30). Cancellarli falserebbe lo storico.
_APPEND_ONLY = {"finance_journal", "privacy_registro_trattamenti", "board_revenue_events",
                "kbot_conversions", "kbot_conversations", "hr_analytics_snapshots",
                "corporate_acts", "compliance_training", "training_records"}

# Canali esterni riconosciuti per un'azione (instradata a n8n, non al DB).
_EXTERNAL_CANALI = {"n8n", "esterno", "external", "webhook"}
# Canali Meta (Instagram publish/commenti, Ads) → API Meta dirette, sempre su conferma.
_META_CANALI = {"instagram", "meta_ads", "meta"}

# delete consentita SOLO per chiave d'identità (riga singola), mai per colonne generiche
# (status/sector/...) → impossibile una cancellazione di massa.
_DELETE_KEYS = {"id", "uuid"}


def is_meta_action(action: Any) -> bool:
    return (isinstance(action, dict)
            and str(action.get("canale") or "").lower() in _META_CANALI)


def is_external_action(action: Any) -> bool:
    """True se l'azione va eseguita FUORI dal DB (pubblica/invia/social/ads). Richiede un
    'canale' ESPLICITO: una chiave 'workflow' da sola non basta (evita che un campo vagante
    dell'LLM instradi per sbaglio all'esterno). Include n8n e i canali Meta → tutte queste
    passano SEMPRE per la conferma umana."""
    if not isinstance(action, dict):
        return False
    c = str(action.get("canale") or "").lower()
    return c in _EXTERNAL_CANALI or c in _META_CANALI


# Segnaposto mai risolti dall'LLM ({{uuid}}, {{now_iso}}, {{month}}, ${nome}…). Scritti
# in DB danno righe inutilizzabili o un 400 da PostgREST; mandati fuori via n8n finiscono
# in una email al cliente. Vanno intercettati PRIMA di eseguire.
_PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}|\$\{[^}]*\}")


class ActuatorError(RuntimeError):
    pass


def segnaposto(valore: Any) -> str | None:
    """Primo segnaposto non risolto nel valore (ricorsivo su dict/list), o None."""
    if isinstance(valore, str):
        m = _PLACEHOLDER.search(valore)
        return m.group(0) if m else None
    if isinstance(valore, dict):
        valore = list(valore.values())
    if isinstance(valore, (list, tuple)):
        for v in valore:
            trovato = segnaposto(v)
            if trovato:
                return trovato
    return None


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
    # Template non risolti: non si scrive un record con "{{uuid}}" dentro.
    ph = segnaposto(data) or segnaposto(match)
    if ph:
        raise ActuatorError(f"valore segnaposto non risolto: {ph}")
    # delete consentita SOLO sotto approvazione umana (apply_action gira all'approve),
    # con match obbligatorio (niente cancellazioni di massa) e MAI su registri immutabili.
    if op == "delete":
        if table in _APPEND_ONLY:
            raise ActuatorError(f"delete vietata su registro immutabile: {table}")
        if not isinstance(match, dict) or not match:
            raise ActuatorError("delete richiede un match (niente cancellazioni di massa)")
        # match SOLO per chiave d'identità (id/uuid) → garantita una sola riga.
        # Una colonna generica (status/sector/...) cancellerebbe in massa: vietata.
        if set(match.keys()) - _DELETE_KEYS:
            raise ActuatorError("delete consentita solo per chiave univoca "
                                f"(id/uuid), non per {sorted(match.keys())}")
        return table, op, match, data
    if op not in ALLOWLIST[table]:
        raise ActuatorError(f"operazione '{op}' non consentita su {table}")
    if not isinstance(data, dict) or not data:
        raise ActuatorError("dati mancanti")
    if op == "update" and (not isinstance(match, dict) or not match):
        raise ActuatorError("update richiede un match (niente update di massa)")
    return table, op, match, data


def preflight(action: dict[str, Any]) -> None:
    """Verifica a monte che l'azione sia eseguibile DAVVERO: perimetro (validate) più
    mappatura sui campi reali della tabella (_sanitize a vuoto). Serve a non mettere in
    coda una proposta che all'Approva non potrebbe scrivere niente — meglio un task
    onesto che una riga fantasma. Solleva ActuatorError se non è eseguibile."""
    table, op, _match, data = validate(action)
    if op != "delete":
        _sanitize(table, data, op)


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


# ---- Robustezza: l'LLM a volte inventa nomi colonna/valori → 400 da PostgREST.
# Mappiamo i sinonimi alle colonne reali, scartiamo le colonne inesistenti (ripiegate
# in un campo note se c'è) e normalizziamo i valori enum. Schema reale per tabella:
_SCHEMA: dict[str, set[str]] = {
    "board_tasks": {"lead_id", "title", "notes", "priority", "status", "due_at", "position", "goal_id"},
    "aios_goals": {"title", "description", "parent_goal_id", "status", "priority"},
    "board_cost_items": {"name", "amount_eur", "frequency", "category", "active"},
    "pipeline_leads": {"name", "company", "sector", "channel", "pain_point", "offer_fit",
                       "status", "score", "next_action", "next_action_date", "notes",
                       "email", "value_eur", "expected_close_date", "last_contact_at"},
    "invoices": {"number", "client_name", "project_id", "amount_eur", "status",
                 "issued_at", "due_at", "paid_at"},
    "finance_journal": {"data", "descrizione", "conto", "dare", "avere", "categoria", "riferimento"},
    "project_tasks": {"project_id", "title", "status", "due_date", "completed_at"},
    "project_phases": {"project_id", "name", "status", "phase_order", "date_completed", "date_estimated"},
    "candidates": {"full_name", "role_applied", "status", "source", "cv_url", "notes"},
    "employees": {"full_name", "role", "department", "hire_date", "contract_type",
                  "contract_end_date", "status", "weekly_capacity_hours"},
    "legal_documents": {"tipo", "controparte", "stato", "rischio", "scadenza", "file_url", "note"},
    "vendors": {"name", "paese_hq", "dpa_status", "dpa_signed_at", "scc", "note"},
    "team_members": {"name", "role", "weekly_capacity_hours", "cost_per_hour", "active"},
    "change_requests": {"project_id", "requested_by", "description", "impact_days", "impact_eur", "status"},
    "project_tools": {"project_id", "tool_name", "licence_cost_monthly", "renewal_date"},
    "trademarks": {"name", "type", "nice_classes", "jurisdiction", "filing_no", "expiry_date", "status"},
    "corporate_acts": {"tipo", "data", "oggetto", "delibere", "signed_at"},
    "disputes": {"controparte", "tipo", "claim_amount", "status", "next_deadline",
                 "prescription_date", "notes"},
    "insurance_policies": {"tipo", "insurer", "premium_annual", "coverage_amount", "expiry_date", "notes"},
    "compliance_training": {"person_email", "training_type", "completed_at", "expires_at"},
    "policy_register": {"policy_name", "version", "effective_date", "review_due_date", "owner"},
    "leave_requests": {"employee_id", "type", "date_start", "date_end", "status", "days"},
    "performance_reviews": {"employee_id", "period", "reviewer", "score", "notes", "next_actions"},
    "skills_matrix": {"employee_id", "skill", "level", "target_level"},
    "training_records": {"employee_id", "course", "provider", "cost_eur", "completed_at"},
    "safety_compliance": {"obligation", "last_done", "due_date", "responsible", "status"},
    "offboarding_events": {"employee_id", "termination_date", "reason", "tfr_amount_eur", "equipment_returned"},
    "hr_analytics_snapshots": {"period", "headcount", "turnover_rate", "avg_time_to_hire_days",
                               "cost_per_hire_eur", "absenteeism_pct"},
    "marketing_prospects": {"company", "website", "sector", "fit_score", "fit_reason",
                            "contact_email", "contact_role", "email_source", "draft_subject",
                            "draft_body", "status"},
    "marketing_competitors": {"name", "website", "offering", "positioning", "pricing",
                              "strengths", "weaknesses", "threat", "differentiation",
                              "source", "status"},
    "aios_content_calendar": {"canale", "titolo", "bozza", "stato", "data_programmata",
                              "fonte_tipo", "fonte_id", "note"},
    "shared_memory": {"key", "value", "category", "updated_by"},
    "privacy_registro_trattamenti": {"trattamento", "base_giuridica", "categorie_dati",
                                     "retention", "responsabile", "note"},
}
_NOTE_COLS = ("notes", "note", "descrizione", "fit_reason", "pain_point")
_SYN: dict[str, tuple[str, ...]] = {
    "title": ("task", "titolo", "oggetto", "attivita", "compito", "azione"),
    "name": ("nome", "azienda", "ragione_sociale", "voce", "servizio", "societa", "cliente"),
    "full_name": ("nome", "name", "nominativo", "candidato"),
    "company": ("azienda", "societa", "ragione_sociale"),
    "client_name": ("cliente", "azienda", "company"),
    "notes": ("motivo", "descrizione", "description", "dettagli", "dettaglio", "nota", "commento"),
    "note": ("motivo", "descrizione", "dettagli", "nota", "commento"),
    "descrizione": ("description", "desc", "dettagli", "motivo"),
    "description": ("descrizione", "desc", "dettagli", "motivo"),
    "amount_eur": ("importo", "importo_eur", "amount", "budget_mese", "budget", "costo",
                   "valore", "value_eur", "importo_totale"),
    "status": ("stato",), "priority": ("priorita",), "email": ("mail", "e_mail"),
    "sector": ("settore",),
}
_PRIORITY = {"alta": "alta", "high": "alta", "critical": "alta", "urgent": "alta", "urgente": "alta",
             "p1": "alta", "media": "media", "medium": "media", "normal": "media", "normale": "media",
             "p2": "media", "bassa": "bassa", "low": "bassa", "p3": "bassa"}
_ENUM = {"board_tasks": {"priority": {"alta", "media", "bassa"},
                         "status": {"todo", "doing", "done", "cancelled"}}}


def _sanitize(table: str, data: dict, op: str = "insert") -> dict:
    """Adatta i dati alle colonne/valori reali della tabella (l'LLM ne inventa)."""
    cols = _SCHEMA.get(table)
    if not cols or not isinstance(data, dict):
        return data
    d = dict(data)
    for canon, aliases in _SYN.items():          # sinonimi → colonna canonica
        if canon in cols and not d.get(canon):
            for a in aliases:
                if a in d and d[a] not in (None, ""):
                    d[canon] = d.pop(a)
                    break
    known = {k: v for k, v in d.items() if k in cols}
    extra = {k: v for k, v in d.items() if k not in cols}
    # Se NESSUN campo dell'LLM finisce su una colonna reale con un valore, ripiegare
    # tutto nel campo note produce una riga con ogni colonna utile a null: è così che
    # in performance_reviews è finita una riga con employee_id/period/score vuoti e le
    # note piene di segnaposto. Meglio non scrivere: il chiamante ripiega su un task.
    utili = {k: v for k, v in known.items() if v not in (None, "", [], {})}
    if extra and not utili:
        raise ActuatorError(f"nessun campo di {table} riconosciuto: {sorted(extra)[:6]}")
    note_col = next((c for c in _NOTE_COLS if c in cols), None)
    if extra and note_col:                        # gli extra non vanno persi
        txt = "; ".join(f"{k}: {v}" for k, v in extra.items() if v not in (None, "", [], {}))
        if txt:
            known[note_col] = ((str(known[note_col]) + " — ") if known.get(note_col) else "") + txt
    for col, allowed in _ENUM.get(table, {}).items():   # valori enum validi (o default DB)
        if col in known:
            v = str(known[col]).strip().lower()
            if col == "priority":
                v = _PRIORITY.get(v, v)
            known[col] = v if v in allowed else known.pop(col)
    if op == "insert" and "title" in cols and not known.get("title"):
        known["title"] = str(known.get(note_col) if note_col else "Attività")[:160] or "Attività"
    if not known:
        raise ActuatorError(f"nessuna colonna valida per {table}")
    return known


def apply_action(client: Any, action: dict[str, Any]) -> dict[str, Any]:
    """Esegue l'azione su Supabase. DDL (tipo='ddl'|chiave 'sql') → modifica schema
    guardata; altrimenti insert/update di righe su tabella allowlist."""
    if isinstance(action, dict) and (action.get("tipo") == "ddl" or action.get("sql")):
        return apply_ddl(str(action.get("sql", "")))
    # Azione META (Instagram publish/commenti, Ads) → API Meta dirette. Gira solo qui,
    # cioè sotto approvazione umana. Le ads sono create SEMPRE in PAUSA (non spendono).
    if is_meta_action(action):
        from aios.sources.meta_actions import apply as meta_apply
        out = meta_apply(action)
        return {"ok": bool(out.get("ok")), "canale": "meta", "esito": out,
                "errore": out.get("errore")}
    # Azione ESTERNA (pubblica/invia/social/gestionale) → instradata a n8n. Gira solo
    # qui, cioè sotto approvazione umana (apply_action è chiamata all'approve).
    if is_external_action(action):
        from aios.sources.n8n import trigger_n8n
        wf = str(action.get("workflow") or "k2ai")
        payload = action.get("payload") or action.get("dati") or {}
        # Verso l'esterno i segnaposto sono peggio che in DB: finirebbero in una email
        # o in un post. Meglio non partire e dirlo.
        ph = segnaposto(payload)
        if ph:
            return {"ok": False, "canale": "n8n", "workflow": wf,
                    "errore": f"segnaposto non risolto nel payload: {ph}"}
        out = trigger_n8n(wf, payload if isinstance(payload, dict) else {})
        return {"ok": bool(out.get("ok")), "canale": "n8n", "workflow": wf, "esito": out}
    table, op, match, data = validate(action)
    if op == "delete":
        # eq. esatto per ogni chiave di match → niente cancellazioni di massa
        filters = {k: f"eq.{v}" for k, v in match.items()}
        rows = client.delete(table, filters)
        return _esito_righe(table, "delete", rows, match=match)
    data = _sanitize(table, data, op)
    if op == "insert":
        rows = client.insert(table, data)
        return {"ok": True, "tabella": table, "op": "insert", "righe": rows}
    # update: SOLO uguaglianza esatta (eq.) per ogni chiave di match — niente operatori
    # passthrough (in./gte./...) → impossibile un update di massa via match crafted.
    filters = {k: f"eq.{v}" for k, v in match.items()}
    rows = client.update(table, filters, data)
    return _esito_righe(table, "update", rows, match=match)


def _esito_righe(table: str, op: str, rows: Any, *, match: dict) -> dict[str, Any]:
    """Esito di un update/delete: 0 righe toccate NON è un successo.

    PostgREST risponde 200 con lista vuota quando il match non trova niente (riga
    inesistente, tabella vuota, id sbagliato). Dichiararlo 'ok' ha fatto passare per
    fatte 6 modifiche a policy_register su una tabella vuota: qui diventa un
    fallimento esplicito, così Telegram e l'audit lo riportano."""
    n = len(rows) if isinstance(rows, list) else rows
    out: dict[str, Any] = {"tabella": table, "op": op, "match": match, "righe": rows}
    if n == 0:
        out["ok"] = False
        out["errore"] = f"nessuna riga di {table} corrisponde al match {match}"
    else:
        out["ok"] = True
    return out
