"""Orchestrator **datacenter / server room** (categoria DIMOSTRATIVA).

12ª tipologia (Tappa 3 Fase 2). Server room e piccoli datacenter: alimentazione BT
dedicata, UPS online doppia conversione (≥15 min), GE standby N+1, ATS rete-UPS-GE,
raffreddamento critico. Continuità di servizio massima.

GAP NORMATIVO NOTO (case study §13.17 + ADR-024): la norma di riferimento dei
datacenter **EN 50600** NON è caricata in KB (PDF non disponibili). Questa tipologia
applica il pattern con le norme disponibili (CEI 64-8, CEI 99-2, IEC 60364) e marca
l'asseverazione come **dimostrativa / non valida per certificazione Tier III/IV
ANSI-TIA-942 o EN 50600**. Pipeline BT + ATS + UPS (`dimensiona_ups`, no cabina MT).
Tool dedicati EN 50600 (PUE, ridondanza tier, raffreddamento) NON esistono: rinviati.
"""
from __future__ import annotations

from .._core.base_orchestrator import BaseOrchestrator

NORME_AGGIUNTIVE = [
    "CEI 64-8 (impianti BT)", "CEI 99-2 (locali tecnici)", "IEC 60364 (best practices)",
    "CEI EN 60947-6-1 (ATS)",
    "NOTA: EN 50600 NON applicata (non in KB) — asseverazione DIMOSTRATIVA",
]


class DatacenterOrchestrator(BaseOrchestrator):
    CAMPI_CRITICI = [
        "A_anagrafica_contesto.committente",
        "A_anagrafica_contesto.indirizzo",
        "C_sorgenti_carichi.carico.P_kW",
    ]
    DEFAULTS_TIPOLOGICI: dict[str, dict] = {
        "C_sorgenti_carichi.carico.contemporaneita": {
            "valore": 0.90, "norma_ref": "datacenter (carico IT continuo + raffreddamento)"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 1.0, "norma_ref": "CEI 64-8 art.411 (TN-S, equipotenzialità rack/PDU)"},
        "D_impianti_protezioni.criterio_selettivita": {
            "valore": "selettività totale", "norma_ref": "continuità di servizio massima"},
    }
    # BT + ATS rete-UPS-GE (no cabina MT). UPS/raffreddamento/PUE come requisito
    # asseverativo (tool EN 50600 dedicati assenti: gap §13.17).
    PIPELINE_STANDARD = [
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "derivazione"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "derivazione"},
        {"tool": "coordinamento_atrs_fv_generatore", "condizione": "ha_ats", "iterazione": None},
        {"tool": "dimensiona_ups", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_selettivita_catena", "condizione": "sempre", "iterazione": None},
        {"tool": "corrente_guasto_terra_mt", "condizione": "sempre", "iterazione": None},
        {"tool": "dispersore_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_terra", "condizione": "sempre", "iterazione": None},
    ]
