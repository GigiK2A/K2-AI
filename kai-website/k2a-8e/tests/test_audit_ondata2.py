"""Regressione audit ondata 2 (eval espansione internazionale NaturaViva, 15 lug 2026).

- tempi corrotti: '048h' (0-48h col trattino perso dal modello locale) → 'entro 48 ore'
- numeri del cliente detti in chat (case_facts) protetti dal grounding
- numeri hard-financial inventati rimossi (N/D) anche sui boost qualitativi (StrategyBoost)
"""
from __future__ import annotations

from app import quality


# ── tempi corrotti ────────────────────────────────────────────────────────────────

def test_sanitize_ore_corrotte():
    d = {"piano": "Agire nelle prime 048h, poi entro 0180h rivedere."}
    out = quality.sanitize_corrupted_time_ranges(d)
    assert "048h" not in out["piano"] and "entro 48 h" in out["piano"]
    assert "entro 180 h" in out["piano"]


def test_sanitize_non_tocca_ore_valide_e_giorni():
    d = {"a": "entro 48 ore", "b": "180 giorni di rodaggio", "c": "alle 09:30"}
    out = quality.sanitize_corrupted_time_ranges(d)
    assert out == d  # nessun match → invariato


def test_sanitize_walk_annidato():
    d = {"fasi": [{"quando": "048h", "cosa": "kickoff"}]}
    out = quality.sanitize_corrupted_time_ranges(d)
    assert out["fasi"][0]["quando"].startswith("entro 48")


# ── grounding con numeri della chat (case_facts) ────────────────────────────────────

def _chat_inputs():
    # ciò che il cliente ha DETTO in chat, come lo passa il K-BOT in contesto_consulenza
    return {"ragione_sociale": "NaturaViva",
            "contesto_consulenza": {
                "sintesi_caso": {"target": "Paesi Bassi 150-200k, sconto 28%, resi 5%"},
                "diagnosi": {"nota": "margine ecommerce 22%"}}}


def test_numeri_detti_in_chat_sono_grounded():
    known = quality.grounded_numbers(_chat_inputs(), {}, [])
    for n in (150000.0, 200000.0, 28.0, 5.0, 22.0):
        assert round(n, 4) in known, f"{n} dovrebbe essere grounded dal contesto chat"


def test_numero_del_cliente_non_viene_rimosso():
    known = quality.grounded_numbers(_chat_inputs(), {}, [])
    # il report riporta CORRETTAMENTE il target del cliente
    v = quality._neutralize_value("target Paesi Bassi €200.000 di ricavi", known, hard_only=True)
    assert "200.000" in v and "N/D" not in v


def test_numero_inventato_hard_rimosso_su_qualitativo():
    known = quality.grounded_numbers(_chat_inputs(), {}, [])
    # l'LLM inventa 500k (mai detto) al posto del 150-200k reale
    v = quality._neutralize_value("stima ricavi €500.000 in Paesi Bassi", known, hard_only=True)
    assert "500.000" not in v and "N/D" in v


def test_kpi_soft_inventato_resta_per_etichetta_su_qualitativo():
    known = quality.grounded_numbers(_chat_inputs(), {}, [])
    # CPL/conversion inventati: soft → NON rimossi qui (verranno etichettati dallo scrub)
    v = quality._neutralize_value("conversione attesa 4% sul traffico", known, hard_only=True)
    assert "4%" in v and "N/D" not in v


def test_deep_neutralize_hard_only_su_dict():
    known = quality.grounded_numbers(_chat_inputs(), {}, [])
    d = {"scenari": [{"txt": "EBITDA incrementale €500.000"}],
         "kpi": [{"txt": "conversione 4%"}]}
    out = quality.neutralize_ungrounded_numbers(d, _chat_inputs(), {}, [], hard_only=True)
    assert "500.000" not in out["scenari"][0]["txt"]   # hard inventato → via
    assert "4%" in out["kpi"][0]["txt"]                # soft → resta
