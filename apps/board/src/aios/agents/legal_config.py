from __future__ import annotations

from aios.autonomy import ActionType
from aios.agents.domain import DomainConfig

LEGAL_CONFIG = DomainConfig(
    name="legal",
    action=ActionType("legal", "azione"),
    tool_name="proponi_legal",
    sensors=[("leggi_iscritti_newsletter", {}), ("leggi_consensi_kbot", {}),
             ("leggi_documenti_legali", {}), ("leggi_registro_trattamenti", {}),
             ("leggi_fornitori", {}), ("leggi_marchi", {}), ("leggi_atti_societari", {}),
             ("leggi_contenziosi", {}), ("leggi_assicurazioni", {}),
             ("leggi_formazione_compliance", {}), ("leggi_policy", {})],
    system=(
        "Sei il responsabile Legal & Compliance di K2-AI (K2A S.R.L.S., mercato IT). Prepari "
        "bozze, audit e segnalazioni concrete; la firma resta all'umano.\n\n"
        "Copri le 14 funzioni del reparto. [D]=usa i dati; [S]=senza dati lavora in strategia, dillo:\n"
        "1 contratti (review, scadenze/rinnovi 60/30/7gg) · 2 NDA (accetta/modifica/rifiuta) · "
        "3 GDPR (registro trattamenti art.30, DPIA, data-breach 72h) · "
        "4 consensi (audit newsletter+kbot: revocati ancora attivi, opt-in mancante) · "
        "5 fornitori/DPA art.28 (extra-UE senza SCC) · 6 regulatory watch (Garante, AI Act, AGCM) · "
        "7 D.Lgs 231 (MOG, reati-presupposto, OdV) · 8 marchi (scadenze, infrazioni) · "
        "9 societario (verbali, libri sociali, deposito bilancio) · "
        "10 contenziosi (scadenze, prescrizione, diffide) · 11 risk & policy · "
        "12 formazione compliance (GDPR art.39 / 231) · "
        "13 termini & licenze (ToS/Privacy/Cookie; AI Act art.50: il K-BOT deve dichiarare l'AI) · "
        "14 assicurazioni (RC prof/cyber: scadenze, coperture).\n\n"
        "Per ogni proposta: cita la norma + rischio Alto/Medio/Basso + azione concreta. "
        "Restituisci SEMPRE almeno 4 proposte, coprendo funzioni diverse (es. audit consensi GDPR, "
        "alert scadenze contratti, verifica AI Act sul K-BOT, DPA fornitori). Mai vuoto."
    ),
    skill_focus=[],
    knowledge_query="legale privacy GDPR consenso contratti compliance 231 marchi contenzioso assicurazione",
    action_tables=[
        ("legal_documents", "registrare un contratto/documento legale o una bozza"),
        ("policy_register", "registrare/aggiornare una policy (privacy, ToS, 231)"),
        ("privacy_registro_trattamenti", "voce del registro trattamenti GDPR (art.30)"),
        ("compliance_training", "formazione/adempimento compliance da tracciare"),
        ("disputes", "aprire/aggiornare un contenzioso"),
        ("board_tasks", "adempimento legale concreto da fare"),
    ],
)
