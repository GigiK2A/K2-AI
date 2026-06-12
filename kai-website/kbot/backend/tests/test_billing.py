"""Test logica billing (pura, no DB/Stripe). Verifica regole abbonamento/crediti
contro il modello fonte (catalogo_documenti.json)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.lib import billing as b  # noqa: E402


def test_free_non_esegue():
    assert b.puo_eseguire_servizi("free") is False
    assert b.puo_eseguire_servizi(None) is False
    assert b.puo_eseguire_servizi("pro") is True
    assert b.puo_eseguire_servizi("business") is True


def test_sconti_boost():
    assert b.sconto_boost_pct("free") == 0
    assert b.sconto_boost_pct("pro") == 10
    assert b.sconto_boost_pct("business") == 20
    # LegalBoost 490€ → Pro 441 · Business 392
    assert b.prezzo_boost_scontato(490, "pro") == 441
    assert b.prezzo_boost_scontato(490, "business") == 392
    assert b.prezzo_boost_scontato(490, None) == 490


def test_crediti_mensili():
    assert b.crediti_mensili("pro") == 50
    assert b.crediti_mensili("business") == 200
    assert b.crediti_mensili("free") == 0


def test_boost_mai_a_crediti():
    boost = {"strato": "servizio", "prezzo_documento_eur": 490}
    assert b.costo_crediti(boost) is None  # i Boost NON si pagano a crediti


def test_check_a_crediti():
    check = {"strato": "consumo", "prezzo_documento_eur": 19}
    assert b.costo_crediti(check) == 19  # 1 cr = 1€
    check2 = {"strato": "consumo", "costo_crediti": 49}
    assert b.costo_crediti(check2) == 49


def test_pacchetti():
    assert b.pacchetto_crediti(199) == {"prezzo_eur": 199, "crediti": 220, "consigliato": True}
    assert b.pacchetto_crediti(1234) is None


def test_load_model_fallback_e_catalog():
    m = b.load_model(None)
    assert m["fonte"].startswith("costanti") and "pro" in m["piani"]
    cat = {"abbonamenti": {"piani": {"pro": {"prezzo_mese_eur": 49}}},
           "crediti": {"valore_credito_eur": 1}}
    m2 = b.load_model(cat)
    assert m2["fonte"] == "catalog.json"


def _run():
    fns = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    ok = 0
    for fn in fns:
        fn(); ok += 1; print(f"  {fn.__name__} OK")
    print(f"\nBILLING: {ok}/{len(fns)} test passati")
    return 0


if __name__ == "__main__":
    raise SystemExit(_run())
