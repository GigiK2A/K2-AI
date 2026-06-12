"""Orchestrator impianto **fotovoltaico connesso in BT** (utente attivo CEI 0-21).

Variante BaseOrchestrator. FV sempre presente, parallelo rete BT, SPI/anti-islanding.
Il tool SPI è `verifica_spi_cei_021` (esiste nei 32 tool: nessun gap).
"""
from __future__ import annotations

from .._core.base_orchestrator import BaseOrchestrator

NORME_AGGIUNTIVE = ["CEI 0-21:2025-04 (utente attivo BT)",
                    "Regola tecnica anti-islanding (SPI)", "DM 37/2008"]


class FvBtOrchestrator(BaseOrchestrator):
    CAMPI_CRITICI = [
        "A_anagrafica_contesto.committente",
        "A_anagrafica_contesto.indirizzo",
        "C_sorgenti_carichi.carico.P_kW",
    ]
    DEFAULTS_TIPOLOGICI: dict[str, dict] = {
        "C_sorgenti_carichi.rifasamento_cosphi_target": {
            "valore": 0.95, "norma_ref": "CEI 0-21 (cosφ nominale richiesto dal DSO)"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 20.0, "norma_ref": "CEI 64-8 art.411 (TT)"},
    }
    PIPELINE_STANDARD = [
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "verifica_spi_cei_021", "condizione": "sempre", "iterazione": None},
        {"tool": "dispersore_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_spd_coordinato", "condizione": "ha_fotovoltaico", "iterazione": None},
    ]
