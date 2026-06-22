"""Orchestrator impianto **fotovoltaico connesso in MT** (utente attivo CEI 0-16).

Tappa 3 Fase 2 — settima tipologia. Impianto FV grande (tipico 800–5000 kW) connesso
direttamente in MT tramite cabina di consegna (CDS) con trafo elevatore BT/MT.
Differisce da `fv_bt` per: connessione MT, norma CEI 0-16 (non 0-21), Protezione
Generale (PG) e Sistema di Protezione Generale (SPG) MT, selettività totale.

GAP TOOL CHIUSO (ADR-022, Sessione 27): la pipeline usa ora i tool MT dedicati
`verifica_protezione_generale_mt` (SPG/PG, CEI 0-16 §8.8 + Allegato 2b Tab.1) e
`verifica_protezione_interfaccia_mt` (SPI MT, §8.8.7.2 Tab.12) al posto del precedente
workaround `verifica_spi_cei_021` (SPI BT 0-21). `verifica_selettivita_catena` resta
per la selettività cronometrica tra livelli. La pipeline esclude ancora il
dimensionamento delle stringhe DC (il tool `dimensiona_cavo` è AC-trifase): rinviato.
"""
from __future__ import annotations

from .._core.base_orchestrator import BaseOrchestrator

NORME_AGGIUNTIVE = ["CEI 0-16:2025-04 (utente attivo MT)",
                    "Regola tecnica anti-islanding (SPG)",
                    "CEI EN 62305-2 (rischio fulmine, impianto outdoor)"]


class FvMtOrchestrator(BaseOrchestrator):
    CAMPI_CRITICI = [
        "A_anagrafica_contesto.committente",
        "A_anagrafica_contesto.indirizzo",
        "B_allacciamento_sistema.tensione_MT_kV",
        "C_sorgenti_carichi.carico.P_kW",
    ]
    DEFAULTS_TIPOLOGICI: dict[str, dict] = {
        "B_allacciamento_sistema.Icc_MT_kA": {
            "valore": 12.5, "norma_ref": "CEI 0-16 §5.2.1.3 (provvisorio, TICA)"},
        "C_sorgenti_carichi.rifasamento_cosphi_target": {
            "valore": 0.95, "norma_ref": "CEI 0-16 (fattore di potenza -0,95..+0,95)"},
        "D_impianti_protezioni.criterio_selettivita": {
            "valore": "selettività totale", "norma_ref": "CEI 0-16 (utente attivo MT)"},
        "D_impianti_protezioni.impianto_terra.Re_target_ohm": {
            "valore": 1.0, "norma_ref": "CEI EN 50522 / CEI 64-8 art.411"},
    }
    # Pipeline (~11 step). dimensiona_trafo escluso (elevatore dimensionato dal FV, non
    # dal carico ausiliario); icc_bt_multisorgente escluso (FV non contribuisce a Icc
    # post-SPG). Interfaccia/generale MT via i tool dedicati CEI 0-16 (ADR-022):
    # verifica_protezione_generale_mt (PG) + verifica_protezione_interfaccia_mt (SPI MT).
    PIPELINE_STANDARD = [
        {"tool": "calcola_icc_cabina", "condizione": "sempre", "iterazione": None},
        {"tool": "dimensiona_cavo", "condizione": "sempre", "iterazione": "servizi_aux"},
        {"tool": "caduta_tensione", "condizione": "sempre", "iterazione": "servizi_aux"},
        {"tool": "verifica_protezione", "condizione": "sempre", "iterazione": "servizi_aux"},
        {"tool": "verifica_protezione_generale_mt", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_protezione_interfaccia_mt", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_selettivita_catena", "condizione": "sempre", "iterazione": None},
        {"tool": "dispersore_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_terra", "condizione": "sempre", "iterazione": None},
        {"tool": "valuta_rischio_fulmine", "condizione": "sempre", "iterazione": None},
        {"tool": "verifica_spd_coordinato", "condizione": "ha_fotovoltaico", "iterazione": None},
    ]
