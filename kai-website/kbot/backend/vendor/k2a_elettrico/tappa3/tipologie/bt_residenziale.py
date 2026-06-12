"""Orchestrator cabina/impianto BT **residenziale** (condomini, edifici BT).

Variante BaseOrchestrator. Allacciamento BT diretto da DSO (no MT, no trafo, no GE),
sistema TT, contemporaneità bassa. Pipeline solo BT (montante + derivazioni).
"""
from __future__ import annotations

from .._core.base_orchestrator import BaseOrchestrator

NORME_AGGIUNTIVE = ["CEI 64-8 parte 7 (ambienti residenziali)", "DM 37/2008"]


class BtResidenzialeOrchestrator(BaseOrchestrator):
    CAMPI_CRITICI = [
        "A_anagrafica_contesto.committente",
        "A_anagrafica_contesto.indirizzo",
        "C_sorgenti_carichi.carico.P_kW",
    ]
    DEFAULTS_TIPOLOGICI: dict[str, dict] = {
        "C_sorgenti_carichi.carico.contemporaneita": {
            "valore": 0.40, "norma_ref": "prassi residenziale (coincidenza appartamenti)"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 20.0, "norma_ref": "CEI 64-8 art.411 (sistema TT, RA·Idn≤U_lim)"},
    }
    PIPELINE_STANDARD = [
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "derivazione"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "derivazione"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "derivazione"},
        {"tool": "dispersore_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_terra", "condizione": "sempre", "iterazione": None},
    ]
