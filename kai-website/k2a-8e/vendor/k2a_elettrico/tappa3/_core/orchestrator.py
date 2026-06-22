"""Orchestrator per cabina MT/BT **industriale** (variante di BaseOrchestrator).

Fornisce solo i dati specifici della tipologia (campi critici, default, pipeline);
la logica generica vive in `base_orchestrator.BaseOrchestrator`. I simboli comuni
(dataclass, helper) sono ri-esportati qui per retro-compatibilità degli import.
"""
from __future__ import annotations

from .base_orchestrator import (  # noqa: F401 (re-export)
    BaseOrchestrator,
    OrchestrationResult,
    StatoValidazione,
    ToolPipelineStep,
    ValidazioneResult,
    _campo_presente,
    _get,
)


class CabinaIndustrialeOrchestrator(BaseOrchestrator):
    """Orchestratore deterministico per cabina MT/BT industriale."""

    CAMPI_CRITICI = [
        "A_anagrafica_contesto.committente",
        "A_anagrafica_contesto.indirizzo",
        "B_allacciamento_sistema.tensione_MT_kV",
        "C_sorgenti_carichi.carico.P_kW",
    ]

    DEFAULTS_TIPOLOGICI: dict[str, dict] = {
        "B_allacciamento_sistema.Icc_MT_kA": {
            "valore": 12.5, "norma_ref": "CEI 0-16 §5.2.1.3 (valore tipico DSO, da confermare)"},
        "C_sorgenti_carichi.carico.contemporaneita": {
            "valore": 0.8, "norma_ref": None},
        "C_sorgenti_carichi.rifasamento_cosphi_target": {
            "valore": 0.95, "norma_ref": "CEI 0-16 (soglia penali DSO)"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 1.0, "norma_ref": "CEI 64-8 art.411"},
    }

    PIPELINE_STANDARD = [
        {"tool": "dimensiona_trafo", "condizione": "sempre", "iterazione": None},
        {"tool": "calcola_icc_cabina", "condizione": "sempre", "iterazione": None},
        {"tool": "icc_bt_multisorgente", "condizione": "multi_sorgente", "iterazione": None},
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "arrivo_bt"},
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "linea_generale"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "arrivo_bt"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "linea_generale"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "arrivo_bt"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "linea_generale"},
        {"tool": "coordinamento_atrs_fv_generatore", "condizione": "ha_ats", "iterazione": None},
        {"tool": "verifica_spi_cei_021", "condizione": "ha_fotovoltaico", "iterazione": None},
        {"tool": "verifica_selettivita_catena", "condizione": "sempre", "iterazione": None},
        {"tool": "corrente_guasto_terra_mt", "condizione": "sempre", "iterazione": None},
        {"tool": "dispersore_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "valuta_rischio_fulmine", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_spd_coordinato", "condizione": "ha_fotovoltaico", "iterazione": None},
    ]
