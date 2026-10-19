"""Le operazioni scritte nella risposta si rifanno in codice (errori del modello vero, 19/10/2026)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))

from app.lib.aritmetica_guard import correggi

from test_e2e_scenarios import _make_session, client, fake_anthropic, fake_db  # noqa: F401  (fixture)


def test_la_sottrazione_sbagliata_del_caso_reale_si_corregge_e_si_propaga():
    t = ("PFN = 2.130.000 − 140.000 = 2.090.000 €\nPFN/EBITDA = 2.090.000 / 710.000 = 2,94\n"
         "Quindi con una PFN di 2.090.000 euro servono 2,94 anni.")
    assert correggi(t) == ("PFN = 2.130.000 − 140.000 = 1.990.000 €\nPFN/EBITDA = 1.990.000 / 710.000 = 2,80\n"
                           "Quindi con una PFN di 1.990.000 euro servono 2,80 anni.")


@pytest.mark.parametrize("t", [
    "Totale costi: 600.000 + 500.000 + 250.000 + 90.000 = 1.440.000", "DSO = 1.870.000 / 6.200.000 × 365 = 110",
    "2 + 2 = 4", "3,5 x 2 = 7", "1.000 + 2.000 = 3.000 e il resto no", "Il rapporto è 2.800.000 / 1.000.000 = 2,8",
    "A = B = C", "Art. 7 - 5 = ...", "x = y", "il prezzo = 50 euro", "(360.000 / 1.800.000) * 100 = 20%",
    "Stima: 1.990.000 / 710.000 = 2,8 anni (arrotondato)", "12 x 30 = 360",
])
def test_non_tocca_quello_che_torna_o_non_e_un_calcolo_semplice(t):
    assert correggi(t) == t


def test_corregge_un_errore_semplice_e_rispetta_i_decimali():
    assert correggi("Margine: 2.100.000 - 1.635.000 = 460.000") == "Margine: 2.100.000 - 1.635.000 = 465.000"
    assert correggi("2 + 2 = 5") == "2 + 2 = 4"
    assert correggi("1.990.000 / 710.000 = 2,94") == "1.990.000 / 710.000 = 2,80"
    assert correggi("3,5 x 2 = 8,0") == "3,5 x 2 = 7,0"


def test_anche_il_segno_di_approssimazione_si_verifica():
    # caso reale: «1.990.000 / 710.000 ≈ 2,94» (giusto: 2,80); un «≈ 2,8» arrotondato bene resta
    assert correggi("PFN/EBITDA = 1.990.000 ÷ 710.000 ≈ 2,94 anni") == "PFN/EBITDA = 1.990.000 ÷ 710.000 ≈ 2,80 anni"
    assert correggi("1.990.000 ÷ 710.000 ≈ 2,8 anni") == "1.990.000 ÷ 710.000 ≈ 2,8 anni"


def test_precedenza_degli_operatori():
    assert correggi("10 + 5 x 2 = 20") == "10 + 5 x 2 = 20"        # 10 + (5×2) = 20: torna
    assert correggi("10 + 5 x 2 = 30") == "10 + 5 x 2 = 20"


def test_un_risultato_piccolo_non_propaga_altrove():
    t = "50 + 40 = 100. Il termine è di 100 giorni."
    assert correggi(t) == "50 + 40 = 90. Il termine è di 100 giorni."


def test_interruttore(monkeypatch):
    monkeypatch.setenv("KBOT_ARITMETICA", "0")
    assert correggi("2 + 2 = 5") == "2 + 2 = 5"


def test_end_to_end_la_risposta_arriva_corretta(client, fake_anthropic):
    from app.lib.limiter import limiter
    limiter.reset()
    fake_anthropic.canned_text = "La PFN è 2.130.000 − 140.000 = 2.090.000 euro e PFN/EBITDA = 2.090.000 / 710.000 = 2,94."
    sid = _make_session(client)
    r = client.post("/api/kbot/message", json={"session_id": sid, "message": "Calcolami la PFN e l'indice, per favore."})
    m = r.json()["message"]
    assert "= 1.990.000 euro" in m and "= 2,80" in m and "2.090.000" not in m
