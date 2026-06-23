"""Orchestrator impianto **cantiere temporaneo** (CEI 64-8 sez. 706).

8ª tipologia (Tappa 3 Fase 2). Impianti di cantiere edile/demolizione/stradale:
allacciamento BT (no MT, no trafo), sistema **TT sempre**, differenziali 30 mA
obbligatori su tutti gli utilizzatori, IP44 interno / IP67 esterno, nessun LPS
strutturale (impianto temporaneo). Pipeline solo BT (quadro ASC + derivazioni).
"""
from __future__ import annotations

from .._core.base_orchestrator import BaseOrchestrator

NORME_AGGIUNTIVE = [
    "CEI 64-8 sez.706 (cantieri)", "CEI 64-17 (guida cantieri)",
    "CEI 11-27 (PES/PAV)", "D.Lgs. 81/2008 (sicurezza)",
]


class CantiereTemporaneoOrchestrator(BaseOrchestrator):
    CAMPI_CRITICI = [
        "A_anagrafica_contesto.committente",
        "A_anagrafica_contesto.indirizzo",
        "C_sorgenti_carichi.carico.P_kW",
    ]
    DEFAULTS_TIPOLOGICI: dict[str, dict] = {
        "C_sorgenti_carichi.carico.contemporaneita": {
            "valore": 0.70, "norma_ref": "prassi cantiere (utenze concentrate)"},
        "C_sorgenti_carichi.carico.cosphi": {
            "valore": 0.85, "norma_ref": "utensili motorizzati di cantiere"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 20.0, "norma_ref": "CEI 64-8 art.411 (TT, RA·Idn≤U_lim, Idn=30mA)"},
        "D_impianti_protezioni.criterio_selettivita": {
            "valore": "minimale", "norma_ref": "CEI 64-8 sez.706 (impianto temporaneo)"},
    }
    # Pipeline solo BT: quadro generale ASC (montante) + derivazioni utenze.
    # Niente MT/trafo/FV/ATS/fulmini (cantiere temporaneo, no LPS strutturale).
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
