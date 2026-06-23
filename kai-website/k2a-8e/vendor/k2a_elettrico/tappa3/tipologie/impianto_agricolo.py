"""Orchestrator **impianto agricolo** (CEI 64-8 sez. 705).

9ª tipologia (Tappa 3 Fase 2). Serre, allevamenti, magazzini agricoli: allacciamento
BT, sistema TT, FV in autoconsumo opzionale (CEI 0-21), protezione rinforzata zone
animali (tensione di contatto 25 V vs 50 V) e IP65 per umidità/polveri organiche.
"""
from __future__ import annotations

from .._core.base_orchestrator import BaseOrchestrator

NORME_AGGIUNTIVE = [
    "CEI 64-8 sez.705 (ambienti agricoli/zootecnici)",
    "CEI 0-21:2025-04 (FV autoconsumo, se presente)", "DM 37/2008",
]


class ImpiantoAgricoloOrchestrator(BaseOrchestrator):
    CAMPI_CRITICI = [
        "A_anagrafica_contesto.committente",
        "A_anagrafica_contesto.indirizzo",
        "C_sorgenti_carichi.carico.P_kW",
    ]
    DEFAULTS_TIPOLOGICI: dict[str, dict] = {
        "C_sorgenti_carichi.rifasamento_cosphi_target": {
            "valore": 0.95, "norma_ref": "CEI 0-21 (se FV); rifasamento motori"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 10.0, "norma_ref": "CEI 64-8 sez.705 (TT, tensione contatto 25V animali)"},
        "D_impianti_protezioni.criterio_selettivita": {
            "valore": "parziale", "norma_ref": "CEI 64-8 sez.705"},
    }
    # BT + terra + FV opzionale (autoconsumo CEI 0-21) + SPD se FV.
    PIPELINE_STANDARD = [
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "derivazione"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "montante"},
        {"tool": "verifica_spi_cei_021", "condizione": "ha_fotovoltaico", "iterazione": None},
        {"tool": "dispersore_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "valuta_rischio_fulmine", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_spd_coordinato", "condizione": "ha_fotovoltaico", "iterazione": None},
    ]
