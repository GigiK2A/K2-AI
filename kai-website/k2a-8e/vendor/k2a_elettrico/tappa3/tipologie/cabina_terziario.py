"""Orchestrator per cabina MT/BT **terziario** (uffici, retail, hotel).

Variante di BaseOrchestrator: fornisce i dati specifici della tipologia. La logica
generica (validazione, default, pipeline, aggregazione flag) è ereditata.

Differenze principali rispetto all'industriale (vedi ADR-019):
- fattore di contemporaneità 0.60 (vs 0.80) e cosφ medio 0.95 (vs 0.92);
- selettività tipicamente parziale; GE/ATS raramente presenti (default off);
- normativa specifica CEI EN 50171 (illuminazione di emergenza).
"""
from __future__ import annotations

from .._core.base_orchestrator import BaseOrchestrator

# Norme specifiche del terziario (oltre a quelle comuni di cabina).
NORME_AGGIUNTIVE_TERZIARIO = ["CEI EN 50171 (alimentazione sistemi di sicurezza / "
                              "illuminazione di emergenza)"]


class CabinaTerziarioOrchestrator(BaseOrchestrator):
    """Orchestratore deterministico per cabina MT/BT a servizio di edificio terziario."""

    CAMPI_CRITICI = [
        "A_anagrafica_contesto.committente",
        "A_anagrafica_contesto.indirizzo",
        "B_allacciamento_sistema.tensione_MT_kV",
        "C_sorgenti_carichi.carico.P_kW",
    ]

    # Default tipologici TERZIARIO (valori diversi dall'industriale dove indicato).
    DEFAULTS_TIPOLOGICI: dict[str, dict] = {
        "B_allacciamento_sistema.Icc_MT_kA": {
            "valore": 12.5, "norma_ref": "CEI 0-16 §5.2.1.3 (valore tipico DSO, da confermare)"},
        # contemporaneità terziario tipicamente più bassa (carichi diffusi, non motori)
        "C_sorgenti_carichi.carico.contemporaneita": {
            "valore": 0.60, "norma_ref": "prassi terziario (carichi: illuminazione/HVAC/prese)"},
        "C_sorgenti_carichi.rifasamento_cosphi_target": {
            "valore": 0.95, "norma_ref": "CEI 0-16 (soglia penali DSO)"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 1.0, "norma_ref": "CEI 64-8 art.411"},
        # selettività tipicamente parziale nel terziario
        "D_impianti_protezioni.criterio_selettivita": {
            "valore": "cronometrica parziale",
            "norma_ref": "CEI 64-8 §536 (selettività parziale ammessa nel terziario)"},
    }

    # Pipeline: stessi tool dell'industriale; il coordinamento ATS scatta solo se ci
    # sono SIA ATS SIA gruppo elettrogeno (nel terziario è più raro).
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
        {"tool": "coordinamento_atrs_fv_generatore", "condizione": "ha_ats_e_ge", "iterazione": None},
        {"tool": "verifica_spi_cei_021", "condizione": "ha_fotovoltaico", "iterazione": None},
        {"tool": "verifica_selettivita_catena", "condizione": "sempre", "iterazione": None},
        {"tool": "dispersore_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "valuta_rischio_fulmine", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_spd_coordinato", "condizione": "ha_fotovoltaico", "iterazione": None},
    ]
