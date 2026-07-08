"""Policy owner (8 lug 2026): il gate di grounding NON deve MAI bloccare sui VALORI.

Un numero-cliente non ancorato (concentrazione 15%, retention 100%, persino un €/EBITDA
fabbricato dal modello) non fa più refuse: si etichetta illustrativo (scrub non-strict) e
si consegna — anche sui boost FINANZIARI (prima esclusi dall'escape → vicolo cieco pagato).

Questo test blinda l'invariante alla radice del gate (quality/grounding), replicando la
logica dell'escape in pipeline.py: se TUTTI i blocchi sono di classe-valore
(_VALUE_BLOCK_CODES), lo scrub non-strict li etichetta e i blocchi vanno a zero.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import grounding, quality, tax  # noqa: E402
from app.pipeline import _VALUE_BLOCK_CODES  # noqa: E402


def _fiscoboost_full():
    """FiscoBoost in FULL: il binder inietta IRES/aliquota reali (72.000 / 24%) che NON
    sono negli inputs/facts → il gate strict li flagga numero_non_grounded. Prima →
    refuse. Ora → etichetta-e-consegna."""
    d = {
        "sintesi": {"score_fiscale": 65, "carico_fiscale_stimato": 1,
                    "mappa_aree": [{"area": "IVA", "semaforo": "verde"}]},
        "voci": [{"id": "x", "titolo": "T", "contenuto": "analisi",
                  "rischi_opportunita": [], "azioni": [], "fonti": []}],
        "piano_azione": [{"priorita": 1, "azione": "a", "handoff_commercialista": True}],
        "disclaimer": "d",
        "meta": {"servizio": "FiscoBoost", "cliente": "ElettroBari SRL"},
    }
    form = {"forma_giuridica": "srl", "utile_ante_imposte": 300000,
            "ragione_sociale": "ElettroBari SRL"}
    out, _meta = tax.apply_fiscoboost(d, form)
    return out, form


def test_financial_value_blocks_are_labeled_not_refused():
    out, form = _fiscoboost_full()
    facts = {}

    # 1) Gate STRICT (comportamento finanziario pre-scrub): i numeri del binder sono flaggati.
    strict_blocks = grounding.blocks(grounding.integrity_findings(
        out, citazioni=[], inputs=form, facts=facts, strict=True, strict_norme=False))
    assert strict_blocks, "atteso almeno un blocco sui numeri del binder in strict"

    # 2) TUTTI i blocchi sono di classe-valore → l'escape scatta (nessun difetto duro di forma).
    assert all(b.get("code") in _VALUE_BLOCK_CODES for b in strict_blocks), \
        f"blocchi non-valore inattesi: {[b.get('code') for b in strict_blocks]}"

    # 3) Escape: scrub non-strict etichetta i numeri → gate non-strict → ZERO blocchi → consegna.
    labeled = quality.scrub_ungrounded_numbers(out, form, facts, [], strict=False)
    residual = grounding.blocks(grounding.integrity_findings(
        labeled, citazioni=[], inputs=form, facts=facts, strict=False, strict_norme=False))
    assert not residual, f"dopo l'etichettatura NON deve restare alcun blocco: {residual}"


if __name__ == "__main__":
    test_financial_value_blocks_are_labeled_not_refused()
    print("PASS test_never_block_values")
