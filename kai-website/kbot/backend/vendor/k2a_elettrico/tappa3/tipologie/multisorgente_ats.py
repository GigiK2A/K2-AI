"""Orchestrator impianto **multisorgente con ATS** (edifici critici: sanitario,
datacenter, continuità di servizio alta). Rete DSO + GE + FV opzionale + ATS.

Variante BaseOrchestrator: il caso più completo. Pipeline analoga alla cabina
industriale + coordinamento ATS sempre attivo (ATS presente per definizione).
"""
from __future__ import annotations

from .._core.base_orchestrator import BaseOrchestrator

NORME_AGGIUNTIVE = ["CEI EN 50438 (gruppo elettrogeno in parallelo)",
                    "CEI EN 60947-6-1 (commutatore ATS)",
                    "CEI EN 62305-2 (rischio fulmine, edificio critico)"]


class MultisorgenteAtsOrchestrator(BaseOrchestrator):
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
            "valore": 0.70, "norma_ref": "mix carichi edificio critico"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 1.0, "norma_ref": "CEI 64-8 art.411 / CEI EN 50522"},
        "D_impianti_protezioni.criterio_selettivita": {
            "valore": "selettività totale", "norma_ref": "CEI 64-8 §536 (continuità di servizio alta)"},
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
