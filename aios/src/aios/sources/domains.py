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


# ---------------------------------------------------------------- Catalogo prodotti (spina dorsale)
def catalog_tools(client: Any) -> list[Tool]:
    """Catalogo prodotti unico, condiviso con sito + K-BOT (tabella suite_services)."""
    return [
        _ro("leggi_suite", "suite_services",
            {"select": "id,name,short_description,recommended_tier,category,target,pillar_url",
             "order": "id.asc"}, client),
    ]


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
        _ro("leggi_costi", "board_cost_items",
            {"select": "name,amount_eur,frequency,category,active", "active": "eq.true",
             "order": "amount_eur.desc"}, client),
        _ro("leggi_fatture", "invoices",          # accounts receivable
            {"select": "number,client_name,amount_eur,status,issued_at,due_at,paid_at",
             "order": "due_at.asc", "limit": "100"}, client),
        _ro("leggi_giornale", "finance_journal",  # general ledger
            {"select": "data,descrizione,conto,dare,avere,categoria",
             "order": "data.desc", "limit": "100"}, client),
        _ro("leggi_organico", "employees",        # payroll
            {"select": "full_name,role,contract_type,status", "limit": "100"}, client),
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
        _ro("leggi_team", "team_members",
            {"select": "name,role,weekly_capacity_hours,active", "limit": "50"}, client),
        _ro("leggi_change_requests", "change_requests",
            {"select": "project_id,description,impact_days,impact_eur,status",
             "order": "created_at.desc", "limit": "50"}, client),
        _ro("leggi_strumenti", "project_tools",
            {"select": "project_id,tool_name,licence_cost_monthly,renewal_date",
             "order": "renewal_date.asc", "limit": "50"}, client),
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
        _ro("leggi_documenti_legali", "legal_documents",
            {"select": "tipo,controparte,stato,rischio,scadenza", "order": "created_at.desc",
             "limit": "100"}, client),
        _ro("leggi_registro_trattamenti", "privacy_registro_trattamenti",
            {"select": "trattamento,base_giuridica,categorie_dati,retention", "limit": "100"}, client),
        _ro("leggi_fornitori", "vendors",
            {"select": "name,paese_hq,dpa_status,scc", "limit": "100"}, client),
        _ro("leggi_marchi", "trademarks",
            {"select": "name,type,jurisdiction,expiry_date,status", "limit": "50"}, client),
        _ro("leggi_atti_societari", "corporate_acts",
            {"select": "tipo,data,oggetto,signed_at", "order": "data.desc", "limit": "50"}, client),
        _ro("leggi_contenziosi", "disputes",
            {"select": "controparte,tipo,claim_amount,status,next_deadline",
             "order": "next_deadline.asc", "limit": "50"}, client),
        _ro("leggi_assicurazioni", "insurance_policies",
            {"select": "tipo,insurer,coverage_amount,expiry_date", "order": "expiry_date.asc",
             "limit": "50"}, client),
        _ro("leggi_formazione_compliance", "compliance_training",
            {"select": "person_email,training_type,completed_at,expires_at", "limit": "50"}, client),
        _ro("leggi_policy", "policy_register",
            {"select": "policy_name,version,effective_date,review_due_date", "limit": "50"}, client),
    ]


# ---------------------------------------------------------------- HR / People
def hr_tools(client: Any) -> list[Tool]:
    # Tabelle employees/candidates create; se vuote l'agente lavora in consulenza.
    return [
        _ro("leggi_dipendenti", "employees",
            {"select": "full_name,role,department,contract_type,contract_end_date,"
                       "status,weekly_capacity_hours", "limit": "200"}, client),
        _ro("leggi_candidati", "candidates",
            {"select": "full_name,role_applied,status,source,notes", "order": "created_at.desc",
             "limit": "100"}, client),
        _ro("leggi_assegnatari", "tasks",
            {"select": "assigned_to,status,title,priority", "limit": "100"}, client),
        _ro("leggi_ferie", "leave_requests",
            {"select": "employee_id,type,date_start,date_end,status,days",
             "order": "date_start.desc", "limit": "50"}, client),
        _ro("leggi_review", "performance_reviews",
            {"select": "employee_id,period,score,next_actions", "order": "created_at.desc",
             "limit": "50"}, client),
        _ro("leggi_skills", "skills_matrix",
            {"select": "employee_id,skill,level,target_level", "limit": "100"}, client),
        _ro("leggi_formazione", "training_records",
            {"select": "employee_id,course,provider,completed_at", "limit": "50"}, client),
        _ro("leggi_sicurezza", "safety_compliance",
            {"select": "obligation,last_done,due_date,status", "order": "due_date.asc",
             "limit": "50"}, client),
        _ro("leggi_offboarding", "offboarding_events",
            {"select": "employee_id,termination_date,reason,equipment_returned",
             "order": "termination_date.desc", "limit": "50"}, client),
        _ro("leggi_hr_analytics", "hr_analytics_snapshots",
            {"select": "period,headcount,turnover_rate,avg_time_to_hire_days,absenteeism_pct",
             "order": "created_at.desc", "limit": "12"}, client),
    ]
