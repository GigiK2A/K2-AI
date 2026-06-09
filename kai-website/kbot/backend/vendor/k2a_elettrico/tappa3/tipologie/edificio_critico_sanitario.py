"""Orchestrator **edificio critico sanitario** (CEI 64-8 sez. 710).

10ª tipologia (Tappa 3 Fase 2). Ospedali piccoli, case di cura/RSA, day hospital:
cabina MT/BT + gruppo elettrogeno + ATS + UPS (gruppi 0/riserva ≤0,5 s; 60 s UPS).
Locali gruppo 1/2 con sistema IT-M e sorveglianza continua dell'isolamento, tensione
di contatto ≤25 V, equipotenzialità supplementare. Pipeline analoga al multisorgente.

NOTA: il dimensionamento UPS è ora calcolato dal tool `dimensiona_ups` (gruppi 0/riserva).
Il sistema IT-M (sorveglianza isolamento locali gruppo 2) resta un requisito asseverativo
documentato (nessun tool MCP dedicato).
"""
from __future__ import annotations

from .._core.base_orchestrator import BaseOrchestrator

NORME_AGGIUNTIVE = [
    "CEI 64-8 sez.710 (locali ad uso medico)", "CEI EN 60601 (apparecchi medicali)",
    "CEI EN 50438 (GE)", "CEI EN 60947-6-1 (ATS)", "DM 18/09/2002 (sicurezza incendio ospedali)",
]


class EdificioCriticoSanitarioOrchestrator(BaseOrchestrator):
    CAMPI_CRITICI = [
        "A_anagrafica_contesto.committente",
        "A_anagrafica_contesto.indirizzo",
        "B_allacciamento_sistema.tensione_MT_kV",
        "C_sorgenti_carichi.carico.P_kW",
    ]
    DEFAULTS_TIPOLOGICI: dict[str, dict] = {
        "B_allacciamento_sistema.Icc_MT_kA": {
            "valore": 12.5, "norma_ref": "CEI 0-16 §5.2.1.3 (provvisorio, TICA)"},
        "C_sorgenti_carichi.carico.contemporaneita": {
            "valore": 0.70, "norma_ref": "mix carichi struttura sanitaria"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 1.0, "norma_ref": "CEI 64-8 sez.710 (IT-M, contatto ≤25V, equipot. suppl.)"},
        "D_impianti_protezioni.criterio_selettivita": {
            "valore": "selettività totale", "norma_ref": "CEI 64-8 sez.710 (continuità di servizio critica)"},
    }
    PIPELINE_STANDARD = [
        {"tool": "dimensiona_trafo", "condizione": "sempre", "iterazione": None},
        {"tool": "calcola_icc_cabina", "condizione": "sempre", "iterazione": None},
        {"tool": "icc_bt_multisorgente", "condizione": "multi_sorgente", "iterazione": None},
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "arrivo_bt"},
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "linea_generale"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "arrivo_bt"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "arrivo_bt"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "linea_generale"},
        {"tool": "coordinamento_atrs_fv_generatore", "condizione": "ha_ats", "iterazione": None},
        {"tool": "dimensiona_ups", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_selettivita_catena", "condizione": "sempre", "iterazione": None},
        {"tool": "dispersore_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "valuta_rischio_fulmine", "condizione": "sempre", "iterazione": None},
    ]
