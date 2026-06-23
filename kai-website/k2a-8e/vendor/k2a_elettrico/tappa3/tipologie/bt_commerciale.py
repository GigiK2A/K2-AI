"""Orchestrator impianto BT **commerciale** (negozi, ristoranti, piccole attività).

Variante BaseOrchestrator. Come il residenziale (BT diretto, no MT/GE) ma con
contemporaneità più alta e cosφ misto; FV opzionale.
"""
from __future__ import annotations

from .._core.base_orchestrator import BaseOrchestrator

NORME_AGGIUNTIVE = ["CEI 64-8 (impianti BT)", "DM 37/2008"]


class BtCommercialeOrchestrator(BaseOrchestrator):
    CAMPI_CRITICI = [
        "A_anagrafica_contesto.committente",
        "A_anagrafica_contesto.indirizzo",
        "C_sorgenti_carichi.carico.P_kW",
    ]
    DEFAULTS_TIPOLOGICI: dict[str, dict] = {
        "C_sorgenti_carichi.carico.contemporaneita": {
            "valore": 0.70, "norma_ref": "prassi commerciale (contemporaneità più alta)"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 20.0, "norma_ref": "CEI 64-8 art.411 (TT)"},
    }
    PIPELINE_STANDARD = [
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "derivazione"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "derivazione"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "derivazione"},
        {"tool": "verifica_spi_cei_021", "condizione": "ha_fotovoltaico", "iterazione": None},
        {"tool": "dispersore_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_terra", "condizione": "sempre", "iterazione": None},
    ]
