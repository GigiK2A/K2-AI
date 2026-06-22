"""Orchestrator **cabina MT/BT industriale grande potenza** (CEI 0-16 + CEI 99-2).

11ª tipologia (Tappa 3 Fase 2). Grandi industrie con 2+ trasformatori in parallelo,
ridondanza N+1/2×100%, GE standby + ATS sui servizi essenziali, MT 20/30 kV.
Variante "pesante" della cabina industriale: Icc multi-sorgente sempre rilevante.
"""
from __future__ import annotations

from .._core.base_orchestrator import BaseOrchestrator

NORME_AGGIUNTIVE = [
    "CEI 0-16:2025-04 (utente MT)", "CEI 99-2 (cabine MT/BT)",
    "CEI 11-1 (impianti MT)", "CEI EN 60076-8 (parallelo trafi)",
    "CEI EN 62305-2 (rischio fulmine, capannone esteso)",
]


class CabinaMtIndustrialeGrandeOrchestrator(BaseOrchestrator):
    CAMPI_CRITICI = [
        "A_anagrafica_contesto.committente",
        "A_anagrafica_contesto.indirizzo",
        "B_allacciamento_sistema.tensione_MT_kV",
        "C_sorgenti_carichi.carico.P_kW",
    ]
    DEFAULTS_TIPOLOGICI: dict[str, dict] = {
        "B_allacciamento_sistema.Icc_MT_kA": {
            "valore": 16.0, "norma_ref": "CEI 0-16 (industria grande, Pcc DSO elevata)"},
        "C_sorgenti_carichi.carico.contemporaneita": {
            "valore": 0.85, "norma_ref": "industria pesante (carichi continui)"},
        "C_sorgenti_carichi.rifasamento_cosphi_target": {
            "valore": 0.95, "norma_ref": "rifasamento automatico industriale"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 1.0, "norma_ref": "CEI EN 50522 / CEI 64-8 art.411"},
        "D_impianti_protezioni.criterio_selettivita": {
            "valore": "selettività totale", "norma_ref": "CEI 0-16 + CEI 64-8 §536"},
    }
    # Multi-trafo paralleli: icc_bt_multisorgente sempre attivo. ATS sui servizi essenziali.
    PIPELINE_STANDARD = [
        {"tool": "dimensiona_trafo", "condizione": "sempre", "iterazione": None},
        {"tool": "calcola_icc_cabina", "condizione": "sempre", "iterazione": None},
        {"tool": "icc_bt_multisorgente", "condizione": "sempre", "iterazione": None},
        {"tool": "parallelo_trafi_circolazione", "condizione": "sempre", "iterazione": None},
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "arrivo_bt"},
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "linea_generale"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "arrivo_bt"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "arrivo_bt"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "linea_generale"},
        {"tool": "coordinamento_atrs_fv_generatore", "condizione": "ha_ats", "iterazione": None},
        {"tool": "verifica_selettivita_catena", "condizione": "sempre", "iterazione": None},
        {"tool": "corrente_guasto_terra_mt", "condizione": "sempre", "iterazione": None},
        {"tool": "dispersore_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "valuta_rischio_fulmine", "condizione": "sempre", "iterazione": None},
    ]
