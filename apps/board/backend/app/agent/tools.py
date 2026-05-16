"""Anthropic tool definitions for Giuseppina.

Read-only tools execute directly. `propose_*` tools insert a row into
`board_approvals` with status='pending' — Luigi approves them in /approvazioni
before any side-effect happens. `add_memo` is a direct write (memos are facts).
"""
from __future__ import annotations

from typing import Any, Dict, List


TOOLS: List[Dict[str, Any]] = [
    # ── Read-only ────────────────────────────────────────────────────────────
    {
        "name": "list_leads",
        "description": "Elenca i lead, opzionalmente filtrati per status. Status validi: nuovo, contatto, proposta, chiuso_vinto, chiuso_perso.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filtro status (opzionale)."},
                "limit": {"type": "integer", "default": 20, "minimum": 1, "maximum": 100},
            },
        },
    },
    {
        "name": "get_lead",
        "description": "Recupera un singolo lead per id, includendo il contatto collegato se presente.",
        "input_schema": {
            "type": "object",
            "properties": {"id": {"type": "string", "description": "UUID del lead"}},
            "required": ["id"],
        },
    },
    {
        "name": "search_contacts",
        "description": "Cerca contatti per azienda, nome o email (match case-insensitive).",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Termine di ricerca"}},
            "required": ["query"],
        },
    },
    {
        "name": "list_tasks",
        "description": "Elenca i task. Filtri opzionali per status (todo/doing/done/cancelled) e finestra in giorni dalla scadenza.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "due_within_days": {"type": "integer", "minimum": 0, "maximum": 365},
            },
        },
    },
    {
        "name": "list_pending_approvals",
        "description": "Elenca le approvazioni in coda (status=pending).",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "search_memos",
        "description": "Cerca tra i memos su subject, body o tags.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "get_revenue_summary",
        "description": "KPI revenue per periodo: 'mtd' (mese in corso), 'ytd' (anno), 'last_30d'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["mtd", "ytd", "last_30d"],
                    "default": "mtd",
                }
            },
        },
    },
    {
        "name": "list_meetings",
        "description": "Elenca meeting in un intervallo (ISO date). Default: prossimi 30 giorni.",
        "input_schema": {
            "type": "object",
            "properties": {
                "from_date": {"type": "string", "description": "ISO date YYYY-MM-DD"},
                "to_date": {"type": "string", "description": "ISO date YYYY-MM-DD"},
            },
        },
    },
    {
        "name": "fetch_url",
        "description": "Scarica una URL pubblica e restituisce il testo (max ~50KB). Per arricchire dati di un lead/azienda.",
        "input_schema": {
            "type": "object",
            "properties": {"url": {"type": "string", "format": "uri"}},
            "required": ["url"],
        },
    },
    {
        "name": "overview_snapshot",
        "description": "Snapshot completo del board: lead attivi, task urgenti, approvazioni pending, revenue MTD, prossimo meeting, alert.",
        "input_schema": {"type": "object", "properties": {}},
    },
    # ── Write (PROPOSE — creates pending approval) ───────────────────────────
    {
        "name": "propose_new_lead",
        "description": "Propone la creazione di un nuovo lead. Crea un'approvazione pending — Luigi decide.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "contact_company": {"type": "string"},
                "value_eur": {"type": "number"},
                "source": {
                    "type": "string",
                    "enum": ["k_bot", "contact_form", "newsletter", "referral", "outbound", "other"],
                    "default": "other",
                },
                "rationale": {"type": "string", "description": "Perché vale la pena"},
            },
            "required": ["title", "source", "rationale"],
        },
    },
    {
        "name": "propose_lead_update",
        "description": "Propone una modifica a un lead esistente. Crea approvazione pending.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string"},
                "fields_json": {
                    "type": "object",
                    "description": "Mappa campi → nuovi valori (status, probability, value_eur, ecc.)",
                },
                "rationale": {"type": "string"},
            },
            "required": ["lead_id", "fields_json", "rationale"],
        },
    },
    {
        "name": "propose_email_draft",
        "description": "Propone un draft email verso un contatto. Crea approvazione kind=email pending.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to_contact_id": {"type": "string"},
                "subject": {"type": "string"},
                "body_markdown": {"type": "string"},
                "rationale": {"type": "string"},
            },
            "required": ["to_contact_id", "subject", "body_markdown", "rationale"],
        },
    },
    {
        "name": "propose_proposta_commerciale",
        "description": "Propone una proposta commerciale per un lead. Crea approvazione kind=proposta pending.",
        "input_schema": {
            "type": "object",
            "properties": {
                "lead_id": {"type": "string"},
                "body_markdown": {"type": "string"},
                "rationale": {"type": "string"},
            },
            "required": ["lead_id", "body_markdown", "rationale"],
        },
    },
    {
        "name": "propose_task",
        "description": "Propone un nuovo task. Crea approvazione pending.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "due_at": {"type": "string", "description": "ISO datetime"},
                "priority": {
                    "type": "string",
                    "enum": ["alta", "media", "bassa"],
                    "default": "media",
                },
                "lead_id": {"type": "string"},
                "rationale": {"type": "string"},
            },
            "required": ["title", "priority", "rationale"],
        },
    },
    # ── Direct write (memos only) ────────────────────────────────────────────
    {
        "name": "add_memo",
        "description": "Aggiunge un memo (fatto da ricordare). Scrittura diretta, non richiede approvazione.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}, "default": []},
                "contact_id": {"type": "string"},
                "lead_id": {"type": "string"},
            },
            "required": ["subject", "body"],
        },
    },
]


READ_ONLY_TOOL_NAMES = {
    "list_leads",
    "get_lead",
    "search_contacts",
    "list_tasks",
    "list_pending_approvals",
    "search_memos",
    "get_revenue_summary",
    "list_meetings",
    "fetch_url",
    "overview_snapshot",
}
