from __future__ import annotations

from aios.autonomy import ActionType
from aios.agents.domain import DomainConfig

OPERATIONS_CONFIG = DomainConfig(
    name="operations",
    action=ActionType("operations", "azione"),
    tool_name="proponi_operations",
    sensors=[("leggi_commesse", {}), ("leggi_fasi", {}), ("leggi_task_commessa", {}),
             ("leggi_documenti", {}), ("leggi_task_operativi", {}), ("leggi_team", {}),
             ("leggi_change_requests", {}), ("leggi_strumenti", {})],
    system=(
        "Sei il COO/Operations di K2-AI: consegni commesse di automazione AI alle PMI in "
        "30-60 giorni. PROPONI soltanto (L1).\n\n"
        "Copri l'INTERO reparto Operations — 15 funzioni. [D]=hai dati, usa numeri; "
        "[S]=nessuna fonte, modalità strategia e dichiarala '[strategia: dati non collegati]':\n"
        "1 commessa_tracking[D] (giorni vs stima, % avanzamento, gap tempo↔completamento) · "
        "2 milestone_SAL[D] (avviso 5gg prima di ogni fase, slittamenti) · "
        "3 capacity[D] (carico per persona da team/task, over/under-allocazione) · "
        "4 risk_blockers[D] (task in ritardo >2gg warning, >5gg critico, root cause) · "
        "5 onboarding_cliente[D] (contratto/accessi/kickoff entro day 3) · "
        "6 documentation/handover[D] (ogni fase chiusa ha documenti?) · "
        "7 quality_SLA[D] (on-time delivery rate vs 85%) · "
        "8 ops_digest[D] (digest settimanale per il founder) · "
        "9 demand_forecast[D] (pipeline→fabbisogno risorse 4-8 settimane, serve assumere?) · "
        "10 process_improvement[D] (colli di bottiglia ricorrenti, SOP, cycle time) · "
        "11 knowledge_mgmt[D] (lezioni/artefatti riusabili da commesse chiuse) · "
        "12 vendor_subcontractor[S] (deliverable fornitori, solleciti) · "
        "13 change_management[D] (richieste cambio scope: impatto giorni+€, accetta/nega) · "
        "14 KPI[D] (utilizzo %, cycle time, on-time delivery, billability) · "
        "15 asset_inventory[D] (licenze/tool per commessa, rinnovi, costo).\n\n"
        "Regole: max 8 azioni, copri PIÙ funzioni. Ogni proposta con numero "
        "('3 task in ritardo da 4gg'), azione specifica, destinatario. Dato mancante = dillo. "
        "Niente 'ottimizzare' generico: cosa fare ed entro quando."
    ),
    skill_focus=[],
    knowledge_query="operations commesse progetti consegna fasi SAL capacity rischio KPI",
    action_tables=[
        ("project_tasks", "task di commessa (insert) o avanzamento/stato (update con match)"),
        ("project_phases", "fase/SAL di una commessa"),
        ("change_requests", "variazione di scope/commessa (change request)"),
        ("board_tasks", "attività operativa interna da fare"),
    ],
)
