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
import unicodedata
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


def is_autonomous_internal(action: Any) -> bool:
    """True se l'azione è INTERNA e sicura da eseguire senza chiedere: scrittura
    insert/update/upsert su una tabella del board in allowlist.

    Restano SEMPRE alla conferma umana, qualunque sia il livello di autonomia:
    - azioni ESTERNE (n8n, social, email, ads) → mandano roba fuori dall'azienda;
    - DELETE → distruttive;
    - DDL / SQL grezzo → modificano lo schema.

    Regola dell'owner (ago 2026): «non voglio dare autorizzazioni su cose banali; se
    qualcosa legalmente è sbagliata l'agente la sistema e me lo dice». Quindi: tutto
    l'interno è autonomo e viene RIPORTATO, l'esterno resta ad approvazione."""
    if not isinstance(action, dict) or is_external_action(action):
        return False
    if action.get("tipo") == "ddl" or action.get("sql"):
        return False
    op = str(action.get("op") or "insert").lower()
    return op in ("insert", "update", "upsert")


# Segnaposto mai risolti dall'LLM ({{uuid}}, {{now_iso}}, {{month}}, ${nome}…). Scritti
# in DB danno righe inutilizzabili o un 400 da PostgREST; mandati fuori via n8n finiscono
# in una email al cliente. Vanno intercettati PRIMA di eseguire.
# Compresi i merge-field da mail-merge in parentesi quadre: in coda c'era davvero una
# email pronta a partire che iniziava con "Ciao [Name],". Elenco chiuso di parole per
# non prendere per segnaposto un testo legittimo tra parentesi quadre.
_PLACEHOLDER = re.compile(
    r"\{\{[^}]*\}\}|\$\{[^}]*\}"
    r"|\[(?:name|nome|first[_ ]?name|cognome|azienda|company|cliente|email|città|citta)\]",
    re.IGNORECASE)


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
    # L'LLM scrive in italiano e mette la scadenza sotto il nome che gli viene: senza
    # questi sinonimi finiva nelle note e il task nasceva senza data.
    "due_at": ("scadenza", "due_date", "data_scadenza", "deadline", "entro", "termine"),
    # Registro dei trattamenti (GDPR art.30): il modello usa il lessico della norma
    # ("finalità", "base legale"), la tabella quello del DB. Senza mappatura la riga
    # nasceva con `trattamento` vuoto — un registro inservibile.
    "trattamento": ("finalita", "finalità", "descrizione_trattamento", "id_trattamento"),
    "base_giuridica": ("base_legale", "fondamento_giuridico", "base_giuridica_gdpr"),
    "retention": ("conservazione", "durata_conservazione", "periodo_conservazione"),
    "responsabile": ("titolare", "referente", "owner", "destinatari"),
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


# Trattini e meno "tipografici" che i modelli infilano al posto del '-' ASCII:
# non-breaking hyphen (U+2011), en/em dash, minus sign, fullwidth. Dentro una data
# ("2026‑08‑04") PostgREST risponde 400 e l'azione approvata non scrive niente —
# è successo su board_tasks.due_at e su privacy_registro_trattamenti.
_TRATTINI = dict.fromkeys(
    map(ord, "‐‑‒–—―−﹘﹣－"), "-")


def _ascii_trattini(valore: Any) -> Any:
    """Riporta a '-' i trattini tipografici nei valori scalari (ricorsivo)."""
    if isinstance(valore, str):
        return valore.translate(_TRATTINI)
    if isinstance(valore, dict):
        return {k: _ascii_trattini(v) for k, v in valore.items()}
    if isinstance(valore, list):
        return [_ascii_trattini(v) for v in valore]
    return valore


# Una colonna temporale accetta solo una data ISO. Il modello ci scrive dentro
# "48h", "entro 7 giorni", "prossima settimana": Postgres risponde 400 e l'intera
# insert si perde. Meglio la colonna vuota e il testo nelle note.
_ISO_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]|$)")


def _colonna_temporale(nome: str) -> bool:
    return (nome in ("data", "scadenza", "last_done")
            or nome.startswith(("data_", "date_"))
            or nome.endswith(("_at", "_date", "deadline")))


def _valore_ammesso(colonna: str, valore: Any) -> bool:
    """False se il valore non è scrivibile su quella colonna (data non ISO)."""
    if not _colonna_temporale(colonna) or not isinstance(valore, str):
        return True
    return bool(_ISO_DATA.match(valore.strip()))


def _senza_accenti(nome: str) -> str:
    """Chiave di confronto per i nomi di campo: minuscolo e senza diacritici.

    Il modello scrive «priorità», «finalità», «attività»; i sinonimi e le colonne
    sono in ASCII. Senza questa normalizzazione il campo non veniva riconosciuto e
    il valore finiva nelle note: il task nasceva senza priorità e il registro
    privacy senza finalità del trattamento."""
    piatto = unicodedata.normalize("NFKD", nome)
    return "".join(c for c in piatto if not unicodedata.combining(c)).lower()


def _sanitize(table: str, data: dict, op: str = "insert") -> dict:
    """Adatta i dati alle colonne/valori reali della tabella (l'LLM ne inventa)."""
    cols = _SCHEMA.get(table)
    if not cols or not isinstance(data, dict):
        return data
    d = {k: _ascii_trattini(v) for k, v in data.items()}
    # Un campo scritto con l'accento è lo stesso campo: «priorità» → «priorita».
    piatte: dict[str, list[str]] = {}
    for k in d:
        piatte.setdefault(_senza_accenti(k), []).append(k)
    for canon in list(cols):                     # colonna reale scritta con accenti
        if canon in d:
            continue
        for k in piatte.get(_senza_accenti(canon), ()):
            if d.get(k) not in (None, "") and _valore_ammesso(canon, d[k]):
                d[canon] = d.pop(k)
                piatte[_senza_accenti(canon)] = []
                break
    for canon, aliases in _SYN.items():          # sinonimi → colonna canonica
        if canon in cols and not d.get(canon):
            for a in aliases:
                for k in piatte.get(_senza_accenti(a), ()):
                    # "scadenza: 48h" non è una data: resta un extra e va nelle
                    # note col suo nome, invece di far fallire l'insert su due_at.
                    if k in d and d[k] not in (None, "") and _valore_ammesso(canon, d[k]):
                        d[canon] = d.pop(k)
                        break
                if canon in d:
                    break
    known = {k: v for k, v in d.items() if k in cols}
    extra = {k: v for k, v in d.items() if k not in cols}
    # Data non ISO scritta direttamente sulla colonna: retrocede a extra (nelle note).
    for col in [c for c in known if not _valore_ammesso(c, known[c])]:
        extra[col] = known.pop(col)
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
