"""Sensori readonly per i domini non-marketing (Finance, Operations, Legal, HR).

Ogni sensore è un Tool readonly (action_type=None) che legge tabelle reali su
Supabase via PostgREST. Nessuna scrittura: i domini PROPONGONO soltanto (L1).
Dove un dominio non ha ancora dati reali (es. HR), il sensore restituisce quello
che c'è e l'agente lavora in "modalità consulenza" dichiarandolo.
"""
from __future__ import annotations

from typing import Any

from aios.tools import Tool


def _ro(name: str, table: str, params: dict[str, str], client: Any) -> Tool:
    return Tool(name=name, action_type=None, readonly=True,
                run=lambda **_: client.select(table, params))


# ---------------------------------------------------------------- Finance
def finance_tools(client: Any) -> list[Tool]:
    return [
        _ro("leggi_conversioni", "kbot_conversions",
            {"select": "type,amount_eur,email,created_at", "order": "created_at.desc",
             "limit": "100"}, client),
        _ro("leggi_revenue", "board_revenue_events",
            {"select": "amount_cents,currency,status,description,occurred_at",
             "order": "occurred_at.desc", "limit": "100"}, client),
        _ro("leggi_valore_commesse", "projects",
            {"select": "name,client_name,status,value_eur,progress_pct", "order": "value_eur.desc"},
            client),
        _ro("leggi_memoria_finance", "shared_memory",
            {"select": "key,value,category", "category": "in.(finance,costi,budget,obiettivi)",
             "limit": "50"}, client),
    ]


# ---------------------------------------------------------------- Operations
def operations_tools(client: Any) -> list[Tool]:
    return [
        _ro("leggi_commesse", "projects",
            {"select": "id,name,client_name,sector,offer_type,status,progress_pct,"
                       "start_date,end_date_estimated,value_eur,notes", "order": "updated_at.desc"},
            client),
        _ro("leggi_fasi", "project_phases",
            {"select": "project_id,name,status,phase_order,date_estimated,date_completed",
             "order": "phase_order.asc"}, client),
        _ro("leggi_task_commessa", "project_tasks",
            {"select": "project_id,title,status,due_date,completed_at", "order": "due_date.asc"},
            client),
        _ro("leggi_documenti", "project_documents",
            {"select": "project_id,filename,source,created_at", "order": "created_at.desc",
             "limit": "50"}, client),
        _ro("leggi_task_operativi", "tasks",
            {"select": "title,status,assigned_to,priority,created_at",
             "status": "neq.done", "order": "priority.asc", "limit": "60"}, client),
    ]


# ---------------------------------------------------------------- Legal & Compliance
def legal_tools(client: Any) -> list[Tool]:
    return [
        _ro("leggi_iscritti_newsletter", "newsletter_subscribers",
            {"select": "email,confirmed,is_active,newsletter_ai,source,confirmed_at,unsubscribed_at",
             "limit": "200"}, client),
        _ro("leggi_consensi_kbot", "kbot_profiles",
            {"select": "email,privacy_accepted,privacy_accepted_at,terms_accepted,"
                       "marketing_accepted,marketing_accepted_at", "limit": "200"}, client),
    ]


# ---------------------------------------------------------------- HR / People
def hr_tools(client: Any) -> list[Tool]:
    # Nessuna tabella HR dedicata: l'unico segnale reale sono i task assegnati.
    # L'agente lo dichiara e lavora in modalità consulenza/processo.
    return [
        _ro("leggi_assegnatari", "tasks",
            {"select": "assigned_to,status,title,priority", "limit": "100"}, client),
    ]
